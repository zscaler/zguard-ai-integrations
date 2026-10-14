/*
 * init-config.js — Phase 1: resolve configuration.
 *
 * Reads caller-supplied flow variables (set by the proxy before the
 * FlowCallout) and the FlowCallout `type` parameter, applies defaults, and
 * publishes a normalised aiguard.cfg.* namespace the rest of the flow reads.
 *
 * KVM-GetAIGuardConfig has already populated aiguard.token (and an optional
 * aiguard.policyId) from the encrypted `aiguard-config` map; those are the
 * fallbacks here.
 *
 * Caller-overridable flow variables (all optional):
 *   scanType | type ......... "prompt" | "response" | "both"  (phase)
 *   aiguardCloud ............ cloud region: us1 (default), us2, eu1, eu2
 *   aiguardEndpoint ......... full host override, wins over aiguardCloud
 *   aiguardPolicyId ......... pin one policy id — normally leave unset
 *   scanTools ............... "true"/"false" — fold tool results into scans (default true)
 *   failOpen ................ "true"/"false" — allow on scan failure (default false)
 *   aiguardUser ............. end-user identity sent with the scan (e.g. an email)
 *   appName ................. application label for logs (default "Gateway")
 *   agentId / agentVersion .. optional agent identifiers for logs
 *   aiguardDescriptions ..... JSON string of custom detector descriptions
 */

function cfg(name, dflt) {
    var v = context.getVariable(name);
    if (v === null || v === undefined || v === '') { return dflt; }
    return v;
}

/* ---- phase --------------------------------------------------------------- *
 * Two ways to express the phase, in priority order:
 *   1. FlowCallout parameter `type` ("user-prompt" | "response-prompt" | "both")
 *   2. scanType flow variable ("prompt" | "response" | "both")
 * They normalise to aiguard.cfg.phase = "prompt" | "response" | "both", which
 * in turn decides the scan direction: prompt -> IN, response -> OUT.
 */
var typeParam = cfg('type', '');            // FlowCallout <Parameter name="type">
var scanType  = cfg('scanType', '');
var phase;
if (typeParam === 'response-prompt' || scanType === 'response') { phase = 'response'; }
else if (typeParam === 'both' || scanType === 'both')           { phase = 'both'; }
else                                                            { phase = 'prompt'; }
context.setVariable('aiguard.cfg.phase', phase);

/* ---- endpoint (cloud region) --------------------------------------------- *
 * The detection API lives at api.<cloud>.zseclipse.net. aiguardEndpoint is a
 * full-host escape hatch; otherwise the host is built from the cloud name.
 */
var endpoint = cfg('aiguardEndpoint', '');
if (aiguardIsBlank(endpoint)) {
    endpoint = 'api.' + cfg('aiguardCloud', 'us1') + '.zseclipse.net';
}
context.setVariable('aiguard.cfg.endpoint', endpoint);

/* ---- policy id ----------------------------------------------------------- *
 * Unset is the recommended posture: the API then resolves the policy bound to
 * the API key via /v1/detection/resolve-and-execute-policy. Setting an id
 * switches the call to /v1/detection/execute-policy against that exact id, and
 * an id the key cannot use comes back as "Policy not found" inside an HTTP 200.
 */
var policyId = cfg('aiguardPolicyId', cfg('aiguard.policyId', ''));
context.setVariable('aiguard.cfg.policyId', aiguardIsBlank(policyId) ? '' : String(policyId));

/* ---- booleans (accept real bool or "true"/"false" string) ---------------- */
context.setVariable('aiguard.cfg.scanTools', aiguardTruthy(cfg('scanTools', true)) ? 'true' : 'false');
context.setVariable('aiguard.cfg.failOpen',  aiguardTruthy(cfg('failOpen', false)) ? 'true' : 'false');
// forceAgentHarness: treat all traffic as coming from a coding-agent harness even
// without its headers. Enables <system-reminder> stripping and background-call
// skipping. Only for a proxy DEDICATED to fronting that harness — on a
// general-purpose proxy an attacker could hide a payload in a fake
// <system-reminder> and have it skipped.
context.setVariable('aiguard.cfg.forceHarness',
    aiguardTruthy(cfg('forceAgentHarness', false)) ? 'true' : 'false');
// Posture for requests that cannot be classified (apiType == unknown): default
// off = pass unscanned; on = refuse rather than let unrecognised traffic through.
context.setVariable('aiguard.cfg.failClosedOnUnknown',
    aiguardTruthy(cfg('failClosedOnUnknown', false)) ? 'true' : 'false');
// Block HTTP status: "native" returns the caller's own 200-shaped envelope
// (default, SDK-friendly); a numeric string (e.g. "403") forces a hard status so
// blocks are visible in status-code metrics.
context.setVariable('aiguard.cfg.blockStatus', cfg('blockStatus', 'native'));

/* ---- end-user identity --------------------------------------------------- *
 * Sent with the scan as `user`, so detections are attributed to a person on the
 * AI Guard dashboard. The gateway cannot know who that is on its own: the proxy
 * sets aiguardUser from the identity its own auth established, such as a
 * verified JWT claim. A client-supplied header is a weaker source, since a
 * caller can put any name in it.
 */
context.setVariable('aiguard.cfg.user', cfg('aiguardUser', ''));

/* ---- labels & agent identifiers ------------------------------------------ *
 * These identify the caller in this gateway's own logs, not in the scan record.
 */
context.setVariable('aiguard.cfg.appName', cfg('appName', 'Gateway'));

var agentId = cfg('agentId', '');
if (aiguardIsBlank(agentId)) { agentId = aiguardHeader('X-Agent-ID'); }
context.setVariable('aiguard.cfg.agentId', agentId || '');
context.setVariable('aiguard.cfg.agentVersion', cfg('agentVersion', '') || '');

/* ---- detector descriptions (defaults + optional override) ---------------- *
 * Turns detector names from detectorResponses into readable block messages.
 * Unknown detectors fall back to their raw name, so a detector added upstream
 * still produces a sensible message without a bundle change.
 */
var descriptions = {
    url_cats:          'Malicious or inappropriate URLs detected',
    pii:               'Sensitive personal data detected',
    pii_deepscan:      'Sensitive personal data detected',
    dlp:               'Sensitive data (PII, credentials, secrets) detected',
    secrets:           'Credentials or secrets detected',
    prompt_injection:  'Prompt injection or jailbreak attempt detected',
    toxicity:          'Toxic, hateful, or inappropriate content detected',
    malicious_code:    'Malicious code or command injection detected',
    malicious_url:     'Malicious URL detected',
    agent:             'AI agent manipulation attempt detected',
    topic_violation:   'Content violates topic policies',
    brand_and_reputation_risk: 'Brand or reputation risk detected'
};
var custom = aiguardParse(cfg('aiguardDescriptions', ''));
if (custom) {
    for (var k in custom) {
        if (Object.prototype.hasOwnProperty.call(custom, k)) { descriptions[k] = custom[k]; }
    }
}
context.setVariable('aiguard.cfg.descriptions', aiguardStringify(descriptions));

/* ---- key-presence guard -------------------------------------------------- *
 * KVM-GetAIGuardConfig populated aiguard.token from the encrypted map. If it is
 * missing the flow surfaces a config error in fail-closed mode (RF-ConfigError);
 * in fail-open mode we proceed and the scan fails open downstream.
 */
context.setVariable('aiguard.cfg.keyMissing',
    aiguardIsBlank(cfg('aiguard.token', '')) ? 'true' : 'false');
