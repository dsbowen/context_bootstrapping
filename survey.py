from flask_login import current_user
from hemlock import (
    Branch, Page, Embedded, Blank, Check, Dashboard, Input, Textarea, 
    Label, Debug as D, Validate as V, Navigate as N, binary, likert, route
)
from hemlock.tools import (
    Assigner, Randomizer, attention_check, consent_page, completion_page, make_list, progress
)
from hemlock_berlin import berlin
from hemlock_crt import crt
from hemlock_demographics import basic_demographics
try:
    from yaml import load, CLoader as Loader
except:
    from yaml import load, Loader

from random import shuffle

# percentiles of the distribution predicted by the participant
PERCENTILES = (5, 50, 95)
# number of time-series forecasts made by each participant
N_FCASTS = 6

# templates for the elicitation question with and without context, e.g.,
# pctile=50, 
# fewer_less=fewer, 
# y=thousand new daily COVID-19 cases in the U.S., 
# x_end=on January 1, 2021
# x=days
# output: "There is a 50 in 100 chance that there will be fewer than _____ thousand new daily COVID-19 cases in the U.S. on January 1, 2021."
CONTEXT = (
    'There is a {pctile} in 100 chance that {quantity} will be {fewer_less} than ', ' {y} {x_end} (i.e., at the rightmost point on the graph).'
)
# output: "There is a 50 in 100 chance that the line will be below _____ 5 time steps after the line stops."
NO_CONTEXT = (
    'There is a {pctile} in 100 chance that the line will be below ', ' at the rightmost point on the graph.'
)
# instructions labels
INSTRUCTIONS = {
    'first': {
        'both': open('texts/first_estimate_context_instructions.md', 'r').read(),
        'neither': open('texts/first_estimate_nocontext_instructions.md', 'r').read()
    },
    'second': {
        'both': open('texts/second_estimate_context_instructions.md', 'r').read(),
        'neither': open('texts/second_estimate_nocontext_instructions.md', 'r').read()
    }
}

# 2 (dialectical bootstrapping or no dialectical bootstrapping)
# x 2 (context for both estimates or neither estimate)
assigner = Assigner({
    'Bootstrap': (0, 1),
    'Context': ('both', 'neither')
})
# load forecast questions
forecast_questions = load(open('forecasts.yaml', 'r'), Loader=Loader)
# randomly selects keys for the forecast questions
fcast_selector = Randomizer(list(forecast_questions.keys()), r=N_FCASTS)

# @route('/survey')
def start():
    """
    :return: branch with consent form and preliminary questions
    :rtype: hemlock.Branch
    """
    return Branch(
        consent_page(open('texts/consent.md', 'r').read()),
        Page(attention_check()),
        basic_demographics(page=True),
        *crt(
            'bat_ball', 
            'flowers', 
            'students', 
            'green_round', 
            'stock', 
            'whales', 
            page=True
        ),
        berlin(),
        navigate=first_estimates_branch
    )

@route('/survey')
def first_estimates_branch(start_branch=None):
    """
    :param start_branch: 
    :type start_branch: hemlock.Branch
    :return: branch with first estimate questions
    :rtype: hemlock.Branch
    """
    def make_first_estimate_questions():
        """
        :return: first estimate questions
        :rtype: list of hemlock.Blank
        """
        fcast_keys = fcast_selector.next()
        fcast_keys = (
            list(fcast_keys) if isinstance(fcast_keys, tuple) 
            else [fcast_keys]
        )
        shuffle(fcast_keys)
        current_user.embedded.append(Embedded('Forecast', fcast_keys))
        return [
            (key, make_fcast_questions(key, context, first_estimate=True))
            for key in fcast_keys
        ]

    assigner.next()
    context = use_context(first_estimate=True)
    first_estimate_questions = make_first_estimate_questions()
    return Branch(
        Page(
            Label(INSTRUCTIONS['first'][current_user.meta['Context']])
        ),
        *[
            Page(
                Label(progress(i/N_FCASTS, f'Estimate {i+1} of {N_FCASTS}')),
                Dashboard(
                    src='/dashapp/', 
                    g={'fcast_key': key, 'context': context}
                ),
                *questions,
                timer='FirstEstimateTime'
            ) 
            for i, (key, questions) in enumerate(first_estimate_questions)
        ],
        navigate=N.second_estimates_branch(first_estimate_questions)
    )

def use_context(first_estimate):
    """
    :param first_estimate: indicates whether this is a first estimate (vs second)
    :type first_estimate: bool
    :return: indicates whether to include context
    :rtype: bool
    """
    return (
        (first_estimate and current_user.meta['Context'] == 'both')
        or (not first_estimate and current_user.meta['Context'] != 'neither')
    )

def make_fcast_questions(key, context, first_estimate):
    """Creates forecast questions

    :param key: name of a time-series process
    :type key: str
    :param context: indicates to include context
    :type context: bool
    :param first_estimate: indicates that this is a first estimate
    :type first_estimate: bool
    :return: estimate questions
    :rtype: list of hemlock.Blank
    """
    labels = make_fcast_question_labels(key, context)
    content = forecast_questions[key].copy() # dictionary of question content
    append = get_content_item(content, 'append', 'y') if context else None
    var = 'FirstEstimate' if first_estimate else 'SecondEstimate'
    return [
        Blank(
            label,
            append=append, blank_empty='_____', type='number', step='any',
            var=var+str(pctile), required=True
        )
        for label, pctile in zip(labels, PERCENTILES)
    ]

def make_fcast_question_labels(key, context):
    """Create forecast question labels

    :param key: name of a time-series
    :type key: str
    :param context: indicates to include context
    :type context: bool
    :return: forecast question labels
    :rtype: list of tuple
    """
    def make_question_label(pctile):
        """
        :param pctile: percentile of the distribution being estimated
        :type pctile: scalar
        :return: estimate question label
        :rtype: tuple of (str, str)
        """
        if context:
            return (
                CONTEXT[0].format(
                    pctile=pctile, 
                    fewer_less=fewer_less,
                    quantity=quantity
                ),
                CONTEXT[1].format(y=y, x_end=x_end)
            )
        else:
            return (NO_CONTEXT[0].format(pctile=pctile), NO_CONTEXT[1])

    content = forecast_questions[key].copy() # dictionary of question content
    # x variable text, e.g., 'days'
    x = get_content_item(content, 'x_text', 'x')
    # y variable text, e.g., 'thousand new COVID-19 cases in the U.S.'
    y = get_content_item(content, 'y_text', 'y')
    x_end = content['x_end']
    # fewer or less
    fewer_less = content['fewer_less']
    # name of the quantity, or 'there' e.g., 'there will be...'
    quantity = content.get('quantity', 'there')
    return [make_question_label(pctile) for pctile in PERCENTILES]

def get_content_item(content, key, substitute):
    """Get an item from a question content dictionary

    :param content: time-series content (e.g. name of x and y variables)
    :type content: dict
    :param key: name of a time-series
    :type key: str
    :param substitute: substitute for the key if key is not in content
    :type substitute: str
    :return: item
    :rtype: str
    """
    item = content.get(key)
    if item is None:
        item = content[substitute]
        item = item[0].lower() + item[1:]
    return item

@N.register
def second_estimates_branch(first_estimate_branch, first_estimate_questions):
    """Create branch for second estimates

    :param first_estimate_branch: branch for first estimates
    :type first_estimate_branch: hemlock.Branch
    :param first_estimate_questions: questions containing participant's first estimates
    :type first_estimate_questions: list of (time-series key, question) tuples
    :return: second estimates branch
    :rtype: hemlock.Branch
    """
    def make_instructions_labels():
        """
        :return: instructions labels for second estimates
        :rtype: list of hemlock.Label
        """
        labels = [Label(open('texts/second_estimate.md', 'r').read())]
        if current_user.meta['Context'] == 'second-only':
            labels.append(Label(open('texts/second_estimate_addcontext.md')))
        return labels

    def make_second_estimate_page(i, key, questions):
        """
        :param i: estimate number
        :type i: int
        :param key: name of time-series
        :type key: str
        :param questions: corresponding first estimate questions
        :type questions: list of hemlock.Blank
        :return: page asking for second estimates
        :rtype: hemlock.Page
        """
        labels = make_fcast_question_labels(key, context)
        return Page(
            Label(progress(i/N_FCASTS, f'Estimate {i+1} of {N_FCASTS}')),
            Dashboard(
                src='/dashapp/', 
                g={'fcast_key': key, 'context': context}
            ),
            Label(
                f'''
                Your first estimates were:

                {make_list(
                    [
                        label[0]+q.response+label[1]
                        for label, q in zip(labels, questions)
                    ]
                )}
                '''
            ),
            # additional questions (i.e., for dialectical bootstrapping)
            *make_additional_questions(),
            # estimation questions
            *make_fcast_questions(key, context, first_estimate=False),
            timer='SecondEstimateTime'
        )

    def make_additional_questions():
        """Make additional questions, such as prompts for dialectical bootstrapping

        :return: additional questions
        :rtype: list of hemlock.Question
        """
        if not current_user.meta['Bootstrap']:
            return [Label(
                '''
                Please make second estimates which are different from your first estimates.
                '''
            )]
        return [
            Textarea(
                '''
                Imagine your first estimates were off the mark. Write at least one reason why that could be. Which assumptions or considerations could have been wrong?
                ''',
                var='Assumptions', required=True, validate=V.min_words(7),
                debug=[D.send_keys('here are 7 words without a meaning'), D.send_keys(p_exec=.2)]
            ),
            Check(
                '''
                What does this reason imply? Were your first estimates too high or too low?
                ''',
                [
                    ('Too high', 'high'), 
                    ('Too low', 'low'),
                    ('Some were too high, others too low', 'both')
                ],
                var='Direction', validate=V.require()
            ),
            Label(
                '''
                Based on this new perspective, make second estimates which are different from your first estimates.
                '''
            )
        ]

    context = use_context(first_estimate=False)
    return Branch(
        Page(
            Label(INSTRUCTIONS['second'][current_user.meta['Context']])
        ),
        *[
            make_second_estimate_page(i, key, questions)
            for i, (key, questions) in enumerate(first_estimate_questions)
        ],
        Page(
            *[
                likert(
                    f'Compared to the average person, how much do you know about {forecast_questions[key]["know_about"]}?',
                    [
                        'Much less than average',
                        'Less than average',
                        'About average',
                        'More than average',
                        'Much more than average'
                    ],
                    var='ContextKnowledge'
                )
                for key, _ in first_estimate_questions
            ]
        ),
        Page(
            binary(
                '''
                Did you look up the answers to any of the questions we asked?

                It's important that you answer honestly for research purposes. Your answer won't affect your bonus.
                ''',
                var='LookUp', data_rows=-1,
                validate=V.require()
            ),
            Textarea(
                'Do you have any suggestions for how to improve our study? Feedback is greatly appreciated!',
                var='AdditionalComments', data_rows=-1
            )
        ),
        completion_page()
    )