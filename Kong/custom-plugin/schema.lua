-- kong/plugins/zscaler-aiguard-intercept/schema.lua
local typedefs = require "kong.db.schema.typedefs"

local PLUGIN_NAME = "zscaler-aiguard-intercept"

local schema = {
  name = PLUGIN_NAME,
  fields = {
    { protocols = typedefs.protocols_http },
    { consumer = typedefs.no_consumer },
    {
      config = {
        type = "record",
        fields = {
          { api_key = { type = "string", required = true, encrypted = true }, },
          { api_endpoint = {
              type = "string",
              required = true,
              default = "https://api.us1.zseclipse.net/v1/detection/resolve-and-execute-policy",
            },
          },
          { ssl_verify = { type = "boolean", required = true, default = true }, },
          { timeout_ms = { type = "number", required = false, default = 10000 }, },
        },
      },
    },
  },
}

return schema
