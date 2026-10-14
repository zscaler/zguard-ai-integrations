/*
 * build-aiguard-scan-body.js — Phase 4b: assemble the detection request body.
 *
 * Combines the extracted content (aiguard.promptText / responseText / toolEvent)
 * with the resolved config into the JSON the detection API expects, then stores
 * it as a string (aiguardScanRequestBody) that AM-SetAIGuardScanRequest drops
 * into the ServiceCallout payload verbatim. JSON.stringify handles escaping.
 *
 * The fields sent:
 *
 *     content        the text to scan
 *     direction      "IN"  for prompts and tool arguments
 *                    "OUT" for model responses and tool results
 *     transactionId  optional, must be a 36-character UUID
 *     policyId       optional; present only when a policy id is pinned
 *     user           optional end-user identity, from aiguardUser
 *
 * App name, model and agent identifiers are not sent; they stay in this
 * gateway's logs. The transaction id is what joins a log line to the record in
 * the AI Guard Console.
 */

var apiType = context.getVariable('aiguard.apiType');
var phase   = context.getVariable('aiguard.cfg.phase');

/* ---- content + direction ------------------------------------------------- *
 * One call scans one direction. On "both" the response leg is what this
 * invocation is adjudicating, so it wins; the prompt was already scanned on the
 * request leg by its own FlowCallout.
 */
var promptText   = context.getVariable('aiguard.promptText') || '';
var responseText = context.getVariable('aiguard.responseText') || '';
var content = '';
var direction = 'IN';

if (apiType === 'mcp') {
    /*
     * A tool event is scanned as the text it carries. The scalar values are
     * collected rather than the serialized JSON: a JSON wrapper reads as code to
     * the text detectors and false-positives benign calls. Tool arguments head
     * toward the tool (IN); a tool result re-entering the model is OUT, which is
     * where indirect prompt injection arrives.
     */
    var te = aiguardParse(context.getVariable('aiguard.toolEvent'));
    if (te) {
        var hasOutput = te.output !== null && te.output !== undefined && te.output !== '';
        content = aiguardCollectJoined(te);
        direction = hasOutput ? 'OUT' : 'IN';
    }
} else if (phase === 'response' || (phase === 'both' && responseText.length)) {
    content = responseText;
    direction = 'OUT';
} else {
    content = promptText;
    direction = 'IN';
}

/* ---- transaction id ------------------------------------------------------ *
 * The API rejects a transactionId that is not a standard 36-character UUID with
 * an HTTP 500, and gateway correlation ids are rarely UUIDs. Send ours only when
 * it already is one; otherwise omit the field and let the API mint its own,
 * which JS-ProcessVerdict then records for console correlation.
 */
var UUID_RE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
var txnId = context.getVariable('aiguard.txnId') || '';

var body = { content: content, direction: direction };
if (!aiguardIsBlank(txnId) && UUID_RE.test(String(txnId))) {
    body.transactionId = String(txnId);
}
var policyId = context.getVariable('aiguard.cfg.policyId');
if (!aiguardIsBlank(policyId)) {
    // Present only when pinned; its presence also selects the execute-policy path.
    body.policyId = parseInt(policyId, 10);
}
var user = context.getVariable('aiguard.cfg.user');
if (!aiguardIsBlank(user)) {
    body.user = String(user);
}

context.setVariable('aiguardScanRequestBody', JSON.stringify(body));
context.setVariable('aiguard.scanDirection', direction);
// Republish content presence for the flow's skip condition: extraction may have
// reported content while the built body ends up empty (a tool event that failed
// to parse, for instance), and an empty scan must never be sent.
context.setVariable('aiguard.contentCount', content.length ? '1' : '0');
