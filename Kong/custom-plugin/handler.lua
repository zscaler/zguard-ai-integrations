-- kong/plugins/zscaler-aiguard-intercept/handler.lua

local http = require("resty.http")
local cjson = require("cjson")

local ZscalerAIGuardHandler = {
  PRIORITY = 1000,
  VERSION = "0.1.0",
}

local function log_error(reason, action)
  pcall(function()
    kong.log.error("ZscalerAIGuard: Blocking. Action: " .. tostring(action) .. ", Reason: " .. tostring(reason))
  end)
end

local function perform_scan(config, direction, content_to_scan, transaction_id)
  if not content_to_scan or content_to_scan == "" then
    return "block", "No content available for scanning."
  end

  local payload_table = {
    content = content_to_scan,
    direction = direction,
  }

  if transaction_id and transaction_id ~= "" then
    payload_table.transaction_id = transaction_id
  end

  local request_payload_json, json_err = cjson.encode(payload_table)
  if json_err then
    return "block", "Internal plugin error: Could not encode payload."
  end

  kong.log.debug("ZscalerAIGuard: Scanning payload: " .. request_payload_json)

  local httpc = http.new()
  httpc:set_timeout(config.timeout_ms or 10000)

  local res, err = httpc:request_uri(config.api_endpoint, {
    method = "POST",
    body = request_payload_json,
    headers = {
      ["Content-Type"] = "application/json",
      ["Accept"] = "application/json",
      ["Authorization"] = "Bearer " .. config.api_key,
    },
    ssl_verify = config.ssl_verify,
  })

  if not res then
    local ok, err_keepalive = httpc:set_keepalive()
    if not ok then kong.log.warn("could not set keepalive on failed request: ", err_keepalive) end
    return "block", "AI Guard API call failed: " .. tostring(err)
  end

  local res_body_str = res.body
  local ok, err_keepalive = httpc:set_keepalive()
  if not ok then kong.log.warn("could not set keepalive: ", err_keepalive) end

  if res.status ~= 200 then
    local reason = "AI Guard API returned non-200 status: " .. res.status
    if res_body_str and res_body_str ~= "" then reason = reason .. " Body: " .. res_body_str end
    return "block", reason
  end

  if not res_body_str or res_body_str == "" then
    return "block", "AI Guard API response body was empty, despite 200 OK status."
  end

  local res_body_json, decode_err = cjson.decode(res_body_str)
  if decode_err then
    return "block", "Failed to decode AI Guard API response JSON: " .. tostring(decode_err)
  end

  local action = res_body_json and res_body_json.action
  if not action then
    return "block", "'action' field not found in AI Guard API response."
  end

  kong.log.info("ZscalerAIGuard: Scan result - action: " .. action ..
    ", severity: " .. tostring(res_body_json.severity or "n/a") ..
    ", direction: " .. direction)

  return action, "Verdict received from AI Guard security scan."
end

local function extract_user_prompt(request_body)
  if request_body and request_body.messages and type(request_body.messages) == "table" then
    for i = #request_body.messages, 1, -1 do
      if request_body.messages[i].role == "user" then
        return request_body.messages[i].content
      end
    end
  end
  return nil
end

local function extract_llm_response(response_body_str)
  if not response_body_str then return nil end
  local ok, decoded = pcall(cjson.decode, response_body_str)
  if ok and decoded and decoded.choices and decoded.choices[1] then
    local msg = decoded.choices[1].message
    if msg then return msg.content end
    local delta = decoded.choices[1].delta
    if delta then return delta.content end
  end
  return nil
end

-- ACCESS PHASE: scan the user prompt (direction = IN)
function ZscalerAIGuardHandler:access(config)
  kong.log.info("ZscalerAIGuard: Access phase triggered.")
  kong.service.request.enable_buffering()

  local request_body, err = kong.request.get_body()
  if err or not request_body then
    log_error("Could not get request body: " .. tostring(err), "block")
    return kong.response.exit(400, { message = "Invalid or unreadable request body." })
  end

  local prompt = extract_user_prompt(request_body)
  if not prompt or prompt == "" then
    log_error("Could not find a user prompt in the request payload.", "block")
    return kong.response.exit(400, { message = "No user prompt found in request." })
  end

  local transaction_id = kong.request.get_header("Kong-Request-ID")
    or kong.ctx.shared.request_id
    or ngx.var.request_id

  local action, reason = perform_scan(config, "IN", prompt, transaction_id)

  if action ~= "allow" then
    log_error(reason, action)
    return kong.response.exit(403, {
      message = "Request blocked by Zscaler AI Guard security policy.",
      reason = reason,
    })
  end

  kong.log.info("ZscalerAIGuard: Prompt scan allowed.")
  kong.ctx.shared.request_body = request_body
  kong.ctx.shared.aiguard_transaction_id = transaction_id
end

-- RESPONSE PHASE: scan the LLM response (direction = OUT)
function ZscalerAIGuardHandler:response(config)
  kong.log.info("ZscalerAIGuard: Response phase triggered.")

  local original_request_body = kong.ctx.shared.request_body
  local response_body_str = ngx.ctx.buffered_body

  if not response_body_str then
    kong.log.warn("ZscalerAIGuard: No response body found in response phase.")
    return
  end

  if not original_request_body then
    kong.log.warn("ZscalerAIGuard: Original request context not found. Skipping response scan.")
    return
  end

  local llm_response = extract_llm_response(response_body_str)
  if not llm_response or llm_response == "" then
    kong.log.warn("ZscalerAIGuard: Could not extract LLM response content. Skipping response scan.")
    return
  end

  local transaction_id = kong.ctx.shared.aiguard_transaction_id

  local action, reason = perform_scan(config, "OUT", llm_response, transaction_id)

  if action ~= "allow" then
    log_error(reason, action)
    return kong.response.exit(403, {
      message = "Response blocked by Zscaler AI Guard security policy.",
      reason = reason,
    })
  else
    kong.log.info("ZscalerAIGuard: Response scan allowed.")
  end
end

return ZscalerAIGuardHandler
