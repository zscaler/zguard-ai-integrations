// Extract response from Vertex AI and prepare AI Guard scan payload
var body = context.getVariable('response.content') || '';
var responseText = '';

try {
  var obj = JSON.parse(body);
  if (obj.candidates && Array.isArray(obj.candidates)) {
    for (var i = 0; i < obj.candidates.length; i++) {
      var candidate = obj.candidates[i];
      if (candidate.content && candidate.content.parts && Array.isArray(candidate.content.parts)) {
        for (var j = 0; j < candidate.content.parts.length; j++) {
          if (candidate.content.parts[j].text) {
            responseText += candidate.content.parts[j].text;
          }
        }
      }
    }
  }
} catch (e) {
  responseText = body;
}

// Get configuration. The policy id comes from the KVM only — see scan-prompt.js.
var sessionId = context.getVariable('aiguard.session.id') || context.getVariable('messageid');
var policyId = context.getVariable('private.aiguard.policyid') || '';
var cloud = context.getVariable('aiguard.cloud') || 'us1';

// Build AI Guard API payload for response scan (policyId optional — omit for auto-resolution)
var payload = {
  content: responseText,
  direction: 'OUT'
};

if (policyId && policyId.length > 0) {
  payload.policyId = parseInt(policyId);
}

// Same end-user identity as the prompt scan — see scan-prompt.js.
var user = context.getVariable('aiguardUser') || '';
if (user.length > 0) {
  payload.user = String(user);
}

// Store variables
context.setVariable('aiguard.scan.response.payload', JSON.stringify(payload));
context.setVariable('ai.response', responseText);
context.setVariable('aiguard.response.present', responseText.length > 0 ? 'true' : 'false');
