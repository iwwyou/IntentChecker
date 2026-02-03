const jsPsych = initJsPsych();

// ============================================================
// IntentChecker Developer Survey
// RQ4: Evaluating Intent Model's Expressiveness and Usability
// ============================================================

// Welcome & Consent
var welcome = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h1>IntentChecker: Developer Survey</h1>' +
        '<div style="text-align: left; max-width: 800px; margin: 0 auto; line-height: 1.8;">' +
        '<p>Thank you for participating in this study.</p>' +
        '<p>We are developing <strong>IntentChecker</strong>, a tool that allows developers to specify their intended numeric behaviors in Solidity smart contracts using annotations.</p>' +
        '<p>In this survey, you will:</p>' +
        '<ul>' +
        '<li>Learn about our Intent Annotation Model</li>' +
        '<li>Evaluate code examples with annotations</li>' +
        '<li>Share your opinions on the model\'s expressiveness and usability</li>' +
        '</ul>' +
        '<p>The survey takes approximately <strong>10-15 minutes</strong>.</p>' +
        '<p>By clicking "I Agree", you consent to participate in this study.</p>' +
        '</div>',
    choices: ['I Agree']
};

// Participant Info
var participantInfo = {
    type: jsPsychSurveyText,
    questions: [
        {
            prompt: 'Name (or Pseudonym)',
            name: 'name',
            required: true,
            placeholder: 'Enter your name or pseudonym'
        },
        {
            prompt: 'Email (optional, for follow-up)',
            name: 'email',
            required: false,
            placeholder: 'Enter your email'
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
                'None',
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
            options: ['Undergraduate Student', 'Graduate Student', 'Software Developer', 'Smart Contract Auditor', 'Researcher', 'Other'],
            required: true
        }
    ]
};

// Intent Model Introduction
var intentModelIntro = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>Introduction to Intent Annotations</h2>' +
        '<div style="text-align: left; max-width: 900px; margin: 0 auto; line-height: 1.8;">' +
        '<p>IntentChecker allows developers to express their <strong>intended numeric behaviors</strong> using two types of annotations:</p>' +
        '<h3>1. @During Annotation</h3>' +
        '<p>Specifies intended relationships at specific program points <strong>within</strong> a function.</p>' +
        '<pre style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        '// Example: After this line, fee should be greater than 0\n' +
        'uint256 fee = amount * rate / 100;\n' +
        '<span style="color: green;">// @During fee > 0</span>' +
        '</pre>' +
        '<h3>2. @Post Annotation</h3>' +
        '<p>Specifies intended relationships that should hold <strong>after</strong> function execution.</p>' +
        '<pre style="background: #f5f5f5; padding: 15px; border-radius: 8px; font-size: 14px;">' +
        'function withdraw(uint256 amount) external {\n' +
        '    balances[msg.sender] -= amount;\n' +
        '    msg.sender.transfer(amount);\n' +
        '}\n' +
        '<span style="color: green;">// @Post balances[msg.sender](entry > exit)</span>' +
        '</pre>' +
        '<p>The tool analyzes whether the code satisfies these annotations and reports:</p>' +
        '<ul>' +
        '<li><strong>Satisfied</strong>: The intent always holds</li>' +
        '<li><strong>Violated</strong>: The intent never holds</li>' +
        '<li><strong>Warning</strong>: The intent holds for some inputs but not others (with probability and violation range)</li>' +
        '</ul>' +
        '</div>',
    choices: ['Continue']
};

// Annotation Syntax Reference
var syntaxReference = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<h2>Annotation Syntax Reference</h2>' +
        '<div style="text-align: left; max-width: 900px; margin: 0 auto; line-height: 1.6;">' +
        '<table style="width: 100%; border-collapse: collapse; margin: 20px 0;">' +
        '<tr style="background: #4CAF50; color: white;">' +
        '<th style="padding: 12px; text-align: left;">Annotation</th>' +
        '<th style="padding: 12px; text-align: left;">Meaning</th>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 12px; font-family: monospace;">@During x > 0</td>' +
        '<td style="padding: 12px;">Variable x should be greater than 0 at this point</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 12px; font-family: monospace;">@During x(before > after)</td>' +
        '<td style="padding: 12px;">x should decrease after this statement</td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 12px; font-family: monospace;">@During func.arg[0] > 0</td>' +
        '<td style="padding: 12px;">First argument of func() should be > 0</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 12px; font-family: monospace;">@Post x(entry > exit)</td>' +
        '<td style="padding: 12px;">x should decrease from function entry to exit</td>' +
        '</tr>' +
        '<tr style="background: #f9f9f9;">' +
        '<td style="padding: 12px; font-family: monospace;">@Post unchanged(x)</td>' +
        '<td style="padding: 12px;">x should not change during function execution</td>' +
        '</tr>' +
        '<tr>' +
        '<td style="padding: 12px; font-family: monospace;">@During returnExpression > 0</td>' +
        '<td style="padding: 12px;">Return value should be greater than 0</td>' +
        '</tr>' +
        '</table>' +
        '<p>You can use standard comparison operators: <code>&lt;</code>, <code>&gt;</code>, <code>&lt;=</code>, <code>&gt;=</code>, <code>==</code>, <code>!=</code></p>' +
        '</div>',
    choices: ['Start Evaluation']
};

// Example evaluations
var examples = [
    {
        code: `function calculateFee(uint256 amount, uint256 rate) public pure returns (uint256) {
    uint256 fee = amount / 100 * rate;
    <span style="color: green;">// @During fee > 0</span>
    return fee;
}`,
        title: 'Example 1: Fee Calculation',
        description: 'The developer intends that the calculated fee should always be greater than 0.',
        name: 'fee_calculation'
    },
    {
        code: `function withdraw(uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    <span style="color: green;">// @During balances[msg.sender](before > after)</span>
    msg.sender.transfer(amount);
}`,
        title: 'Example 2: Balance Decrease',
        description: 'The developer intends that the balance should decrease after the subtraction.',
        name: 'balance_decrease'
    },
    {
        code: `function transfer(address to, uint256 amount) external {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;
    balances[to] += amount;
}
<span style="color: green;">// @Post totalSupply(entry == exit)</span>`,
        title: 'Example 3: Total Supply Invariant',
        description: 'The developer intends that total supply remains unchanged after transfer.',
        name: 'total_supply_invariant'
    },
    {
        code: `function distribute(uint256 totalAmount, uint256 numRecipients) external {
    uint256 share = totalAmount / numRecipients;
    for (uint i = 0; i < numRecipients; i++) {
        <span style="color: green;">// @During transfer.arg[0] > 0</span>
        recipients[i].transfer(share);
    }
}`,
        title: 'Example 4: Non-zero Transfer',
        description: 'The developer intends that each transfer amount should be greater than 0.',
        name: 'nonzero_transfer'
    },
    {
        code: `function swap(uint256 amountIn) external returns (uint256 amountOut) {
    amountOut = amountIn * reserveOut / reserveIn;
    <span style="color: green;">// @During amountIn > 0 => amountOut > 0</span>
    reserveIn += amountIn;
    reserveOut -= amountOut;
}`,
        title: 'Example 5: Conditional Intent (Implication)',
        description: 'The developer intends that if input is positive, output should also be positive.',
        name: 'conditional_intent'
    }
];

// Build timeline
var timeline = [welcome, participantInfo, demographics, intentModelIntro, syntaxReference];

// Likert scale options
var likertOptions = [
    'Strongly Disagree',
    'Disagree',
    'Neutral',
    'Agree',
    'Strongly Agree'
];

// Create evaluation trials for each example
for (var i = 0; i < examples.length; i++) {
    var example = examples[i];

    var exampleDisplay = {
        type: jsPsychHtmlButtonResponse,
        stimulus: '<h3>' + example.title + '</h3>' +
            '<div style="text-align: left; max-width: 900px; margin: 0 auto;">' +
            '<p style="color: #666; margin-bottom: 15px;">' + example.description + '</p>' +
            '<pre style="background: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; font-size: 14px; overflow-x: auto;">' +
            example.code +
            '</pre>' +
            '</div>',
        choices: ['Evaluate This Example']
    };
    timeline.push(exampleDisplay);

    var exampleEval = {
        type: jsPsychSurveyLikert,
        questions: [
            {
                prompt: "I can easily understand what this annotation means.",
                name: example.name + '_understand',
                labels: likertOptions,
                required: true
            },
            {
                prompt: "This annotation syntax is intuitive.",
                name: example.name + '_intuitive',
                labels: likertOptions,
                required: true
            },
            {
                prompt: "I have wanted to express this kind of intent when developing smart contracts.",
                name: example.name + '_needed',
                labels: likertOptions,
                required: true
            },
            {
                prompt: "This annotation expresses the developer's intent better than using require/assert alone.",
                name: example.name + '_better_than_require',
                labels: likertOptions,
                required: true
            }
        ],
        data: {
            task: 'example_evaluation',
            example_name: example.name
        }
    };
    timeline.push(exampleEval);
}

// Overall Evaluation
var overallEval = {
    type: jsPsychSurveyLikert,
    preamble: '<h2>Overall Evaluation</h2>' +
        '<p>Based on all the examples you have seen, please rate the following statements:</p>',
    questions: [
        {
            prompt: "The Intent Annotation Model is expressive enough to capture common developer intentions for numeric operations.",
            name: 'overall_expressiveness',
            labels: likertOptions,
            required: true
        },
        {
            prompt: "The annotation syntax is easy to learn.",
            name: 'overall_learnability',
            labels: likertOptions,
            required: true
        },
        {
            prompt: "I would use this kind of annotation in my smart contract development.",
            name: 'overall_willingness',
            labels: likertOptions,
            required: true
        },
        {
            prompt: "This approach is more useful than relying solely on testing or code review.",
            name: 'overall_usefulness',
            labels: likertOptions,
            required: true
        }
    ],
    data: {
        task: 'overall_evaluation'
    }
};
timeline.push(overallEval);

// Open-ended Questions
var openEndedQuestions = {
    type: jsPsychSurveyText,
    preamble: '<h2>Additional Feedback</h2>' +
        '<p>Please share your thoughts on the Intent Annotation Model:</p>',
    questions: [
        {
            prompt: 'Are there any numeric intentions you would like to express but feel the current model cannot support? Please describe.',
            name: 'missing_features',
            required: false,
            rows: 4,
            columns: 60,
            placeholder: 'e.g., "I want to express that variable X should always be a multiple of Y"'
        },
        {
            prompt: 'What improvements or additional features would you suggest for the Intent Annotation Model?',
            name: 'suggestions',
            required: false,
            rows: 4,
            columns: 60,
            placeholder: 'Any suggestions for syntax, new annotation types, or tool features'
        },
        {
            prompt: 'Do you have any other comments or feedback?',
            name: 'other_comments',
            required: false,
            rows: 3,
            columns: 60,
            placeholder: 'Any additional thoughts'
        }
    ],
    data: {
        task: 'open_ended'
    }
};
timeline.push(openEndedQuestions);

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
