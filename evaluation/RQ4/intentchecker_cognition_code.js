const jsPsych = initJsPsych({
    show_progress_bar: true
});

// ============================================================
// Inject global stylesheet into <head> so it survives across trials.
// Putting the <style> tag inside a stimulus would be wiped out when
// jsPsych replaces #jspsych-content.innerHTML on the next trial.
// ============================================================
(function injectGlobalStyles() {
    var css =
        '#jspsych-content { max-width: 100% !important; padding: 0 24px; box-sizing: border-box; }' +
        'body { margin: 0; }' +
        '.jspsych-btn { white-space: normal; }' +
        '@media (max-width: 600px) {' +
        '  #jspsych-content { padding: 0 14px; }' +
        '  h1 { font-size: 22px; }' +
        '  h2 { font-size: 18px; }' +
        '  h3 { font-size: 16px; }' +
        '  p, li, td, label { font-size: 14px; }' +
        '  pre { font-size: 11px !important; padding: 12px !important; line-height: 1.45 !important; }' +
        '  table { font-size: 13px; }' +
        '  th, td { padding: 8px 6px !important; }' +
        '  textarea { font-size: 13px !important; }' +
        '  .jspsych-btn { font-size: 15px; padding: 10px 18px; }' +
        '}';
    var styleEl = document.createElement('style');
    styleEl.setAttribute('data-injected-by', 'intentchecker-survey');
    styleEl.appendChild(document.createTextNode(css));
    document.head.appendChild(styleEl);
})();

// ============================================================
// IntentChecker Developer Survey
// RQ4: Evaluating Intent Model's Expressiveness and Usability
// ============================================================

// Welcome & Consent
var welcome = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h1>IntentChecker: Developer Survey</h1>' +
        '<div style="text-align: left; max-width: 800px; margin: 0 auto; line-height: 1.8;">' +
        '<p>Thank you for taking the time to participate in this survey.</p>' +
        '<p>We are building <strong>IntentChecker</strong>, a <strong>debugging assistant</strong> for Solidity smart contract development.</p>' +
        '<h3 style="margin-top: 20px;">Why this tool?</h3>' +
        '<p>Smart contracts handle real funds, and numeric bugs (precision loss, rounding errors) ' +
        'can lead to direct financial losses. Once deployed, contracts are difficult to modify, ' +
        'so catching these issues <strong>during development</strong> is critical.</p>' +
        '<p>Currently, developers rely on:</p>' +
        '<ul>' +
        '<li><code>require/assert</code> &mdash; only checks at runtime, cannot cover all possible inputs</li>' +
        '<li><code>console.log</code> / event logging &mdash; useful for tracing values, but only for specific test inputs</li>' +
        '<li>Manual code review &mdash; time-consuming and error-prone</li>' +
        '<li>LLM-based review &mdash; helpful, but cannot guarantee correctness (hallucination risk)</li>' +
        '</ul>' +
        '<p><strong>IntentChecker</strong> takes a different approach. Developers write simple annotations ' +
        'expressing their intended numeric behavior (e.g., <code>// @During fee > 0</code> &mdash; "the fee should always be positive"), ' +
        'and the tool <strong>statically analyzes all possible numeric ranges through the code</strong> to check whether the intent holds.</p>' +
        '<p style="color: #666; font-size: 14px;">This tool is currently in the research stage. ' +
        'Future plans include LLM-based automatic annotation suggestion and intent-guided automatic repair.</p>' +
        '<h3 style="margin-top: 20px;">About this survey</h3>' +
        '<p>We want to know: <strong>Would this kind of annotation model actually be useful for you as a developer?</strong></p>' +
        '<p>You will see code examples with annotations and rate them on readability, intuitiveness, and usefulness. ' +
        'The survey takes approximately <strong>10-15 minutes</strong>.</p>' +
        '<p>By clicking "I Agree", you consent to participate.</p>' +
        '</div>',
    choices: ['I Agree']
};

// Participant Info
var participantInfo = {
    type: jsPsychSurveyText,
    questions: [
        {
            prompt: 'Nickname',
            name: 'nickname',
            required: true,
            placeholder: 'Enter a nickname'
        },
        {
            prompt: 'Affiliation (optional)',
            name: 'affiliation',
            required: false,
            placeholder: 'e.g., company, university, community'
        }
    ]
};

// Demographics
var demographics = {
    type: jsPsychSurveyMultiChoice,
    questions: [
        {
            prompt: "How many years of programming experience do you have?",
            name: 'programming_exp',
            options: ['Less than 1 year', '1-2 years', '3-5 years', 'More than 5 years'],
            required: true
        },
        {
            prompt: "What is your experience level with Solidity or smart contracts?",
            name: 'solidity_exp',
            options: [
                'Beginner (read some code)',
                'Intermediate (written some contracts)',
                'Advanced (deployed contracts to mainnet)'
            ],
            required: true
        },
        {
            prompt: "Have you experienced bugs in smart contracts due to numeric calculation errors?",
            name: 'bug_experience',
            options: [
                'Never',
                'Once or twice',
                'Several times',
                'Frequently'
            ],
            required: true
        },
        {
            prompt: "What is your current role?",
            name: 'role',
            options: ['Software Developer', 'Smart Contract Auditor', 'Researcher', 'Student', 'Other'],
            required: true
        }
    ]
};

// Intent Model Introduction
var intentModelIntro = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>How IntentChecker Works</h2>' +
        '<div style="text-align: left; max-width: 900px; margin: 0 auto; line-height: 1.8;">' +
        '<p>IntentChecker uses two types of annotations to express intended numeric behaviors:</p>' +
        '<h3>1. @During &mdash; "At this point in the code..."</h3>' +
        '<p>Checks a condition at a specific line <strong>within</strong> a function. Written as a comment next to the target line.</p>' +
        '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        '<span style="color: #569CD6;">uint256</span> fee = amount * rate / 100; <span style="color: #6A9955;">// @During fee > 0</span>\n' +
        '<span style="color: #C586C0;">return</span> fee;' +
        '</pre>' +
        '<p style="color: #666;">&rarr; "After this calculation, fee should always be greater than 0."</p>' +
        '<h3>2. @Post &mdash; "After the function runs..."</h3>' +
        '<p>Checks a condition by comparing a state variable\'s value <strong>before and after</strong> function execution. Written at the end of the function body.</p>' +
        '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">withdraw</span>(<span style="color: #569CD6;">uint256</span> amount) <span style="color: #569CD6;">external</span> {\n' +
        '    balances[msg.sender] -= amount;\n' +
        '    msg.sender.<span style="color: #DCDCAA;">transfer</span>(amount);\n' +
        '    <span style="color: #6A9955;">// @Post balances[msg.sender](entry > exit)</span>\n' +
        '}' +
        '</pre>' +
        '<p style="color: #666;">&rarr; "After withdraw runs, the user\'s balance should be lower than before."</p>' +
        '<h3 style="margin-top: 25px;">Analysis Results</h3>' +
        '<p>The tool reports one of three outcomes, each with a <strong>risk score (0&ndash;10)</strong> indicating the severity of potential violation:</p>' +
        '<ul>' +
        '<li><strong style="color: #4CAF50;">Satisfied</strong> &mdash; The intent holds for all possible inputs <span style="color: #888;">(Risk: 0.0)</span></li>' +
        '<li><strong style="color: #FF9800;">Warning</strong> &mdash; The intent holds for some inputs but not others <span style="color: #888;">(Risk: 0.1 &ndash; 9.9)</span></li>' +
        '<li><strong style="color: #f44336;">Violated</strong> &mdash; The intent is always broken <span style="color: #888;">(Risk: 10.0)</span></li>' +
        '</ul>' +
        '<p style="color: #666; font-size: 14px;">The risk score reflects the proportion of the input range that violates the intent &mdash; ' +
        'a higher score means a larger portion of inputs can cause unexpected behavior.</p>' +
        '</div>',
    choices: ['Continue']
};

// Analysis Workflow Demo
var analysisDemo = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>How the Analysis Works</h2>' +
        '<div style="text-align: left; max-width: 950px; margin: 0 auto; line-height: 1.8;">' +
        '<p>IntentChecker computes how numeric <strong>ranges</strong> (not individual values) propagate through each operation ' +
        '&mdash; if the input is [1, 1000], it tracks the entire range at once. Here is a complete workflow:</p>' +
        // Step 1
        '<h3>Step 1. Write debug annotations (initial conditions)</h3>' +
        '<p>You specify the input ranges to analyze &mdash; similar to setting up conditions for a test, ' +
        'but the tool checks <strong>all values in the range</strong>, not just specific test cases.</p>' +
        '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        '<span style="color: #6A9955;">// @StateVar feeRate = [1, 100]</span>\n' +
        '<span style="color: #6A9955;">// @LocalVar amount = [1, 1000]</span>' +
        '</pre>' +
        // Step 2
        '<h3>Step 2. Write your intent annotation</h3>' +
        '<p>Express what you expect to hold at a specific point in the code.</p>' +
        '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        '<span style="color: #569CD6;">uint256</span> <span style="color: #569CD6;">public</span> feeRate;\n' +
        '\n' +
        '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">calculateFee</span>(<span style="color: #569CD6;">uint256</span> amount) <span style="color: #569CD6;">public view returns</span> (<span style="color: #569CD6;">uint256</span>) {\n' +
        '    <span style="color: #569CD6;">uint256</span> fee = amount / 100 * feeRate; <span style="color: #6A9955;">// @During fee > 0</span>\n' +
        '    <span style="color: #C586C0;">return</span> fee;\n' +
        '}' +
        '</pre>' +
        // Step 3
        '<h3>Step 3. IntentChecker traces the intervals</h3>' +
        '<p>The tool computes how numeric ranges flow through each operation:</p>' +
        '<div style="background: #f5f5f5; padding: 16px 20px; border-radius: 8px; font-family: monospace; font-size: 14px; line-height: 2;">' +
        '<div><span style="color: #888;">1.</span> amount = <strong>[1, 1000]</strong>, feeRate = <strong>[1, 100]</strong></div>' +
        '<div><span style="color: #888;">2.</span> amount / 100 = <strong>[0, 10]</strong> &nbsp; <span style="color: #e65100;">&larr; integer division: values 1&ndash;99 become 0</span></div>' +
        '<div><span style="color: #888;">3.</span> [0, 10] * feeRate = <strong>[0, 1000]</strong></div>' +
        '<div><span style="color: #888;">4.</span> fee = <strong>[0, 1000]</strong></div>' +
        '</div>' +
        // Result
        '<div style="background: #FFF3E0; border-left: 4px solid #FF9800; padding: 14px 18px; margin-top: 16px; border-radius: 4px; font-size: 15px;">' +
        '<strong>Result:</strong> Intent <code>fee > 0</code> &rarr; ' +
        '<strong style="color: #FF9800;">Warning</strong> <span style="color: #E65100; font-weight: bold;">(Risk: 3.4 / 10)</span> ' +
        '&mdash; fee can be 0 when amount &lt; 100 (due to integer division truncation)' +
        '</div>' +
        // Note
        '<p style="color: #666; font-size: 13px; margin-top: 20px;">' +
        'Unlike runtime assertion tools that check specific test inputs, IntentChecker analyzes <strong>all values in the given range simultaneously</strong> ' +
        'through abstract interpretation.' +
        '</p>' +
        '</div>',
    choices: ['Continue']
};

// Full Intent Model Reference
var syntaxReference = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>Intent Annotation Reference</h2>' +
        '<div style="text-align: left; max-width: 950px; margin: 0 auto; line-height: 1.6;">' +
        '<p>Below is the full set of annotations supported by IntentChecker.</p>' +
        // @During
        '<h3 style="margin-top: 20px;">@During &mdash; Within a Function</h3>' +
        '<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">' +
        '<tr style="background: #2196F3; color: white;">' +
        '<th style="padding: 10px; text-align: left; width: 45%;">Annotation</th>' +
        '<th style="padding: 10px; text-align: left;">Meaning</th>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">@During x > 0</td>' +
        '<td style="padding: 10px;">At this line, x should be greater than 0</td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">@During x(before > after)</td>' +
        '<td style="padding: 10px;">x should decrease after this statement executes' +
        '<br><span style="color: #888; font-size: 13px;">e.g., <code>balance -= fee;</code> &mdash; "before" = balance before subtraction, "after" = balance after</span></td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 10px; font-family: monospace;">@During x(assign > current)</td>' +
        '<td style="padding: 10px;">The value being assigned should be greater than x\'s current value' +
        '<br><span style="color: #888; font-size: 13px;">e.g., <code>price = newPrice;</code> &mdash; "assign" = newPrice, "current" = price before update</span></td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">@During func.arg[0] > 0</td>' +
        '<td style="padding: 10px;">The first argument passed to func() should be greater than 0' +
        '<br><span style="color: #888; font-size: 13px;">e.g., <code>token.transfer(amount)</code> &mdash; checks that amount > 0</span></td>' +
        '</tr>' +
        '</tr>' +
        '</table>' +
        // @Post
        '<h3 style="margin-top: 20px;">@Post &mdash; After Function Execution</h3>' +
        '<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">' +
        '<tr style="background: #2196F3; color: white;">' +
        '<th style="padding: 10px; text-align: left; width: 45%;">Annotation</th>' +
        '<th style="padding: 10px; text-align: left;">Meaning</th>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">@Post x(entry > exit)</td>' +
        '<td style="padding: 10px;">After the function runs, x should be lower than it was before' +
        '<br><span style="color: #888; font-size: 13px;">e.g., in withdraw(): "entry" = balance when function was called, "exit" = balance when function returns</span></td>' +
        '</tr>' +
        '</tr>' +
        '</table>' +
        // Common
        '<h3 style="margin-top: 20px;">Common Clauses &mdash; Usable in Both @During and @Post</h3>' +
        '<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">' +
        '<tr style="background: #2196F3; color: white;">' +
        '<th style="padding: 10px; text-align: left; width: 45%;">Annotation</th>' +
        '<th style="padding: 10px; text-align: left;">Meaning</th>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">returnExpression > 0</td>' +
        '<td style="padding: 10px;">The return value should be greater than 0</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 10px; font-family: monospace;">return[0] > value</td>' +
        '<td style="padding: 10px;">The first return value (for multi-return) should be greater than value</td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">x > PercentOf(y, 90)</td>' +
        '<td style="padding: 10px;">x should be at least 90% of y</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 10px; font-family: monospace;">x > ceil(y, 10) / floor(y, 10)</td>' +
        '<td style="padding: 10px;">x should be greater than the ceiling/floor of y with given precision</td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 10px; font-family: monospace;">x > 0 => y > 0</td>' +
        '<td style="padding: 10px;">If x > 0, then y should also be > 0 (implication)</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 10px; font-family: monospace;">changed(x, true)</td>' +
        '<td style="padding: 10px;">x should have been modified from its initial value' +
        '<br><span style="color: #888; font-size: 13px;">Use <code>changed(x, false)</code> to assert x was NOT modified</span></td>' +
        '</tr>' +
        '</table>' +
        '<p>Supported operators: <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code>, <code>==</code>, <code>!=</code> &nbsp; | &nbsp; ' +
        'Logic connectors: <code>&&</code>, <code>||</code></p>' +
        // Scope
        '<div style="background: #F3E5F5; border-left: 4px solid #9C27B0; padding: 12px 16px; margin-top: 20px; border-radius: 4px;">' +
        '<strong>Scope:</strong> The current model analyzes intents within a <strong>single transaction</strong> &mdash; ' +
        'this includes internal function calls and cross-contract interactions within that transaction. ' +
        'Cross-transaction invariants (e.g., "the sum of all balances should always equal totalSupply across all function calls") ' +
        'are outside the current scope.' +
        '</div>' +
        '<div style="background: #E8F5E9; border-left: 4px solid #4CAF50; padding: 12px 16px; margin-top: 12px; border-radius: 4px;">' +
        '<strong>In practice:</strong> Annotations can be written by developers preemptively during development ' +
        '(e.g., "this fee should be > 0"), or suggested by automated tools such as LLMs given the intent model and source code.' +
        '</div>' +
        '</div>',
    choices: ['Start Examples']
};

// Example code snippets (4 examples matching RQ1 cases)
var examples = [
    {
        code: '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">calculateFee</span>(<span style="color: #569CD6;">uint256</span> amount, <span style="color: #569CD6;">uint256</span> rate) <span style="color: #569CD6;">public pure returns</span> (<span style="color: #569CD6;">uint256</span>) {\n' +
            '    <span style="color: #569CD6;">uint256</span> fee = amount / 100 * rate; <span style="color: #6A9955;">// @During fee > 0</span>\n' +
            '    <span style="color: #C586C0;">return</span> fee;\n' +
            '}',
        title: 'Example 1: Fee Calculation',
        description: 'A function calculates a fee by dividing first, then multiplying. ' +
            'The developer intends that the resulting fee should always be greater than 0.',
        name: 'fee_calculation',
        context: 'If amount is small (e.g., 50) and rate is 1, then 50 / 100 = 0 due to integer division, making fee = 0. ' +
            'IntentChecker would flag this as a <strong>Warning</strong>.'
    },
    {
        code: '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">withdraw</span>(<span style="color: #569CD6;">uint256</span> amount) <span style="color: #569CD6;">external</span> {\n' +
            '    <span style="color: #DCDCAA;">require</span>(balances[msg.sender] >= amount);\n' +
            '    balances[msg.sender] -= amount; <span style="color: #6A9955;">// @During balances[msg.sender](before > after)</span>\n' +
            '    msg.sender.<span style="color: #DCDCAA;">transfer</span>(amount);\n' +
            '}',
        title: 'Example 2: Balance Should Decrease',
        description: 'A withdrawal function subtracts from the user\'s balance. ' +
            'The developer intends that the balance should strictly decrease after the subtraction.',
        name: 'balance_decrease',
        context: 'If amount = 0, require passes but balance stays the same (before == after, not before > after). ' +
            'IntentChecker would flag this as a <strong>Warning</strong>.'
    },
    {
        code: '<span style="color: #569CD6;">uint256</span> <span style="color: #569CD6;">public</span> totalDeposits;\n' +
            '<span style="color: #569CD6;">mapping</span>(<span style="color: #569CD6;">address</span> => <span style="color: #569CD6;">uint256</span>) <span style="color: #569CD6;">public</span> deposits;\n' +
            '\n' +
            '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">refund</span>(<span style="color: #569CD6;">address payable</span> user) <span style="color: #569CD6;">external</span> onlyOwner {\n' +
            '    <span style="color: #569CD6;">uint256</span> amount = deposits[user];\n' +
            '    <span style="color: #C586C0;">if</span> (amount > 0 && user.<span style="color: #DCDCAA;">send</span>(amount)) {\n' +
            '        deposits[user] = 0;\n' +
            '    }\n' +
            '    <span style="color: #6A9955;">// @Post totalDeposits(entry > exit)</span>\n' +
            '}',
        title: 'Example 3: Total Deposits Should Decrease After Refund',
        description: 'A refund function sends deposited ETH back to the user and clears their deposit record. ' +
            'The developer intends that totalDeposits should decrease after a refund.',
        name: 'refund_decrease',
        context: 'The function clears deposits[user] but never updates totalDeposits. ' +
            'IntentChecker would flag this as <strong>Violated</strong>.'
    },
    {
        code: '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">distribute</span>(<span style="color: #569CD6;">uint256</span> totalAmount, <span style="color: #569CD6;">uint256</span> numRecipients) <span style="color: #569CD6;">external</span> {\n' +
            '    <span style="color: #569CD6;">uint256</span> share = totalAmount / numRecipients;\n' +
            '    <span style="color: #C586C0;">for</span> (<span style="color: #569CD6;">uint</span> i = 0; i < numRecipients; i++) {\n' +
            '        recipients[i].<span style="color: #DCDCAA;">transfer</span>(share); <span style="color: #6A9955;">// @During transfer.arg[0] > 0</span>\n' +
            '    }\n' +
            '}',
        title: 'Example 4: Each Transfer Should Be Non-zero',
        description: 'A distribution function divides a total amount equally among recipients. ' +
            'The developer intends that each individual transfer amount should be greater than 0.',
        name: 'nonzero_transfer',
        context: 'If totalAmount < numRecipients, integer division makes share = 0, sending 0 ETH to each recipient. ' +
            'IntentChecker would flag this as a <strong>Warning</strong>.'
    }
];

// Real-world examples drawn from the RQ2 benchmark (Code4rena audits)
var realExamples = [
    {
        code: '<span style="color: #6A9955;">// From Vader Protocol audit (web3bugs #5)</span>\n' +
            '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">calcAsymmetricShare</span>(<span style="color: #569CD6;">uint</span> u, <span style="color: #569CD6;">uint</span> U, <span style="color: #569CD6;">uint</span> A) <span style="color: #569CD6;">public pure returns</span> (<span style="color: #569CD6;">uint</span>) {\n' +
            '    <span style="color: #569CD6;">uint</span> part1    = (u * A);\n' +
            '    <span style="color: #569CD6;">uint</span> part2    = ((U * U) * 2);\n' +
            '    <span style="color: #569CD6;">uint</span> part3    = ((U * u) * 2);\n' +
            '    <span style="color: #569CD6;">uint</span> part4    = (u * u);\n' +
            '    <span style="color: #569CD6;">uint</span> numerator = ((part1 * part2) - part3) + part4;\n' +
            '    <span style="color: #569CD6;">uint</span> part5    = ((U * U) * U);\n' +
            '    <span style="color: #C586C0;">return</span> (numerator / part5); <span style="color: #6A9955;">// @During returnExpression == u*A*(2*U*U - 2*U*u + u*u) / (U*U*U)</span>\n' +
            '}',
        title: 'Real Example 1: Asymmetric Share Formula',
        description: 'From the Vader Protocol audit. The developer implemented a share-of-pool formula and ' +
            'wrote an intent annotation stating the closed-form expression that the return value should equal.',
        name: 'real_asymmetric_share',
        context: 'Expanding the intended formula gives terms <code>2*U<sup>2</sup>*u*A</code>, <code>2*U*u<sup>2</sup>*A</code>, and <code>u<sup>3</sup>*A</code>, ' +
            'but the implemented <code>part3</code> and <code>part4</code> are missing the <code>u*A</code> factor &mdash; ' +
            'each correction term is off by orders of magnitude, so the computed share diverges from the intended value. ' +
            'IntentChecker flags this as <strong>Violated</strong>.'
    },
    {
        code: '<span style="color: #6A9955;">// From Sublime Finance audit (web3bugs #101), simplified</span>\n' +
            '<span style="color: #569CD6;">function</span> <span style="color: #DCDCAA;">_calculatePrincipalWithdrawable</span>(<span style="color: #569CD6;">uint256</span> _id, <span style="color: #569CD6;">address</span> _lender)\n' +
            '    <span style="color: #569CD6;">private view returns</span> (<span style="color: #569CD6;">uint256</span>) {\n' +
            '    <span style="color: #569CD6;">uint256</span> _borrowedTokens            = pooledCLConstants[_id].borrowLimit;\n' +
            '    <span style="color: #569CD6;">uint256</span> _totalLiquidityWithdrawable = _borrowedTokens - POOLED_CREDIT_LINE.<span style="color: #DCDCAA;">getPrincipal</span>(_id);\n' +
            '    <span style="color: #569CD6;">uint256</span> _principalWithdrawable      = _totalLiquidityWithdrawable * <span style="color: #DCDCAA;">balanceOf</span>(_lender, _id) / _borrowedTokens;\n' +
            '    <span style="color: #C586C0;">return</span> _principalWithdrawable; <span style="color: #6A9955;">// @During _principalWithdrawable &lt;= _totalLiquidityWithdrawable</span>\n' +
            '}',
        title: 'Real Example 2: Per-Lender Withdrawable Principal',
        description: 'From the Sublime Finance audit. A lending pool computes how much principal a single lender ' +
            'can withdraw. The intent is that no individual lender\'s withdrawable amount may exceed the pool\'s ' +
            'total available liquidity.',
        name: 'real_principal_withdrawable',
        context: 'When a lender\'s ERC-1155 balance exceeds <code>_borrowedTokens</code> (the pool\'s borrow limit), ' +
            'the multiplication before the division makes <code>_principalWithdrawable</code> strictly larger than ' +
            '<code>_totalLiquidityWithdrawable</code> &mdash; a single lender could withdraw more than the pool holds. ' +
            'IntentChecker flags this as <strong>Violated</strong>.'
    }
];

// Notice shown once before the real-world section
var realCasesNotice = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>Real-World Examples</h2>' +
        '<div style="text-align: left; max-width: 850px; margin: 0 auto; line-height: 1.7;">' +
        '<p>The next two examples come from the actual benchmark used to evaluate IntentChecker &mdash; ' +
        'numeric bugs reported in public Code4rena audits of real DeFi protocols.</p>' +
        '<div style="background: #E3F2FD; border-left: 4px solid #2196F3; padding: 14px 18px; margin: 18px 0; border-radius: 4px;">' +
        '<strong>Note on input ranges.</strong> In real experiments, concrete input ranges (e.g., ' +
        '<code>u = 100</code>, <code>U = 1000</code>, <code>A = 5000</code>) are supplied to the analyzer ' +
        'through <em>debug annotations</em> attached to the function. ' +
        'These are omitted in the snippets below so you can focus on the <strong>intent annotation</strong> itself &mdash; ' +
        'the expression of what the developer thinks the function should compute.' +
        '</div>' +
        '<p style="color: #666; font-size: 14px;">' +
        'Unlike the earlier toy examples, these are drawn directly from production contracts, so the surrounding ' +
        'code and naming may look denser. Focus on the highlighted comment line.' +
        '</p>' +
        '</div>',
    choices: ['Continue']
};

// Build timeline
var timeline = [welcome, participantInfo, demographics, intentModelIntro, analysisDemo, syntaxReference];

// Helper: build a code-example display page
function buildExampleDisplay(example, indexLabel, buttonLabel) {
    return {
        type: jsPsychHtmlButtonResponse,
        stimulus: '<div style="max-width: 900px; margin: 0 auto;">' +
            '<div style="display: flex; justify-content: space-between; align-items: center;">' +
            '<h3>' + example.title + '</h3>' +
            '<span style="color: #999; font-size: 14px;">' + indexLabel + '</span>' +
            '</div>' +
            '<p style="color: #555; margin-bottom: 15px; text-align: left;">' + example.description + '</p>' +
            '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; font-size: 14px; overflow-x: auto; text-align: left;">' +
            example.code +
            '</pre>' +
            '<div style="background: #FFF3E0; border-left: 4px solid #FF9800; padding: 12px 16px; margin-top: 15px; text-align: left; border-radius: 4px;">' +
            '<strong>How IntentChecker helps:</strong> ' + example.context +
            '</div>' +
            '</div>',
        choices: [buttonLabel]
    };
}

// Toy examples
var totalExamples = examples.length + realExamples.length;
for (var i = 0; i < examples.length; i++) {
    var buttonLabel = (i < examples.length - 1) ? 'Next Example' : 'Continue to Real Examples';
    timeline.push(buildExampleDisplay(
        examples[i],
        'Example ' + (i + 1) + ' of ' + totalExamples,
        buttonLabel
    ));
}

// Real-world section: notice + real examples
timeline.push(realCasesNotice);
for (var j = 0; j < realExamples.length; j++) {
    var isLast = (j === realExamples.length - 1);
    var buttonLabel = isLast ? 'Continue to Evaluation' : 'Next Example';
    timeline.push(buildExampleDisplay(
        realExamples[j],
        'Example ' + (examples.length + j + 1) + ' of ' + totalExamples,
        buttonLabel
    ));
}

// Combined Evaluation + Open-ended (single page)
var evaluation = {
    type: jsPsychSurveyHtmlForm,
    preamble: '<h2>Evaluation</h2>' +
        '<p>Based on all the examples and the annotation reference you have seen, please rate the following:</p>',
    html: '<div style="max-width: 900px; margin: 0 auto; text-align: left;">' +
        // Likert questions
        '<table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">' +
        '<tr style="background: #f5f5f5;">' +
        '<th style="padding: 10px; text-align: left; width: 40%;"></th>' +
        '<th style="padding: 8px; text-align: center; font-size: 12px;">Strongly<br>Disagree</th>' +
        '<th style="padding: 8px; text-align: center; font-size: 12px;">Disagree</th>' +
        '<th style="padding: 8px; text-align: center; font-size: 12px;">Neutral</th>' +
        '<th style="padding: 8px; text-align: center; font-size: 12px;">Agree</th>' +
        '<th style="padding: 8px; text-align: center; font-size: 12px;">Strongly<br>Agree</th>' +
        '</tr>' +
        // readability
        '<tr style="border-bottom: 1px solid #eee;">' +
        '<td style="padding: 12px 10px;">The annotations were easy to understand.</td>' +
        '<td style="text-align: center;"><input type="radio" name="readability" value="1" required></td>' +
        '<td style="text-align: center;"><input type="radio" name="readability" value="2"></td>' +
        '<td style="text-align: center;"><input type="radio" name="readability" value="3"></td>' +
        '<td style="text-align: center;"><input type="radio" name="readability" value="4"></td>' +
        '<td style="text-align: center;"><input type="radio" name="readability" value="5"></td>' +
        '</tr>' +
        // relevance
        '<tr style="border-bottom: 1px solid #eee; background: #fafafa;">' +
        '<td style="padding: 12px 10px;">I have wanted to express these kinds of numeric intentions when developing smart contracts.</td>' +
        '<td style="text-align: center;"><input type="radio" name="relevance" value="1" required></td>' +
        '<td style="text-align: center;"><input type="radio" name="relevance" value="2"></td>' +
        '<td style="text-align: center;"><input type="radio" name="relevance" value="3"></td>' +
        '<td style="text-align: center;"><input type="radio" name="relevance" value="4"></td>' +
        '<td style="text-align: center;"><input type="radio" name="relevance" value="5"></td>' +
        '</tr>' +
        // expressiveness
        '<tr style="border-bottom: 1px solid #eee;">' +
        '<td style="padding: 12px 10px;">The annotation model is expressive enough to capture common numeric intentions in smart contracts.</td>' +
        '<td style="text-align: center;"><input type="radio" name="expressiveness" value="1" required></td>' +
        '<td style="text-align: center;"><input type="radio" name="expressiveness" value="2"></td>' +
        '<td style="text-align: center;"><input type="radio" name="expressiveness" value="3"></td>' +
        '<td style="text-align: center;"><input type="radio" name="expressiveness" value="4"></td>' +
        '<td style="text-align: center;"><input type="radio" name="expressiveness" value="5"></td>' +
        '</tr>' +
        // learnability
        '<tr style="border-bottom: 1px solid #eee; background: #fafafa;">' +
        '<td style="padding: 12px 10px;">The annotation syntax would be easy to learn for a new user.</td>' +
        '<td style="text-align: center;"><input type="radio" name="learnability" value="1" required></td>' +
        '<td style="text-align: center;"><input type="radio" name="learnability" value="2"></td>' +
        '<td style="text-align: center;"><input type="radio" name="learnability" value="3"></td>' +
        '<td style="text-align: center;"><input type="radio" name="learnability" value="4"></td>' +
        '<td style="text-align: center;"><input type="radio" name="learnability" value="5"></td>' +
        '</tr>' +
        '</table>' +
        // Open-ended: missing intents
        '<div style="margin-top: 20px;">' +
        '<label style="font-weight: bold; display: block; margin-bottom: 8px;">' +
        'Are there any numeric intentions you would like to express but feel the current annotation model cannot support?' +
        '</label>' +
        '<textarea name="missing_features" rows="4" style="width: 100%; font-size: 14px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" ' +
        'placeholder="e.g., &quot;I want to express that the sum of all balances should equal totalSupply&quot;"></textarea>' +
        '</div>' +
        // Open-ended: suggestions
        '<div style="margin-top: 20px;">' +
        '<label style="font-weight: bold; display: block; margin-bottom: 8px;">' +
        'Any other comments or feedback?' +
        '</label>' +
        '<textarea name="other_comments" rows="3" style="width: 100%; font-size: 14px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;" ' +
        'placeholder="Any additional thoughts"></textarea>' +
        '</div>' +
        '</div>',
    data: {
        task: 'evaluation'
    }
};
timeline.push(evaluation);

// End
var end = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h1>Thank You!</h1>' +
        '<div style="max-width: 600px; margin: 0 auto; line-height: 1.8;">' +
        '<p>Your responses have been recorded.</p>' +
        '<p>Thank you for participating in this study and helping us improve IntentChecker.</p>' +
        '<p>If you have any questions, please contact us at: <strong>iwwyou@korea.ac.kr</strong></p>' +
        '</div>',
    choices: ['Finish']
};
timeline.push(end);

// Run the experiment
jsPsych.run(timeline);
