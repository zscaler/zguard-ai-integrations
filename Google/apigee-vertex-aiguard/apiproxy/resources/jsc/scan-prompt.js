// Extract prompt from Vertex AI request and prepare AI Guard scan payload
var body = context.getVariable('request.content') || '';
var prompt = '';

try {
  var obj = JSON.parse(body);
  if (obj.contents && Array.isArray(obj.contents)) {
    for (var i = 0; i < obj.contents.length; i++) {
      var content = obj.contents[i];
      if (content.parts && Array.isArray(content.parts)) {
        for (var j = 0; j < content.parts.length; j++) {
          if (content.parts[j].text) {
            prompt += content.parts[j].text;
          }
        }
      }
    }
  }
} catch (e) {
  prompt = body;
}

// Get configuration
var sessionId = context.getVariable('request.header.X-Session-ID') || context.getVariable('messageid');
var policyId = context.getVariable('request.header.X-AIGuard-Policy') || context.getVariable('private.aiguard.policyid') || '760';
var vertexModel = context.getVariable('private.vertex.model') || 'gemini-2.5-flash';
var cloud = context.getVariable('private.aiguard.cloud') || 'us1';

// Build AI Guard API payload
var payload = {
  content: prompt,
  direction: 'IN',
  policyId: parseInt(policyId)
};

// Store variables for use in next policies
context.setVariable('aiguard.request.payload', JSON.stringify(payload));
context.setVariable('ai.prompt', prompt);
context.setVariable('aiguard.cloud', cloud);
context.setVariable('aiguard.session.id', sessionId);
