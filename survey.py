from forecasts import forecast_questions

from flask_login import current_user
from hemlock import Branch, Page, Embedded, Blank, Check, Dashboard, Input, Textarea, Label, Validate as V, Navigate as N, route
from hemlock.tools import Assigner, Randomizer, consent_page, completion_page, html_list

from random import shuffle

CONFIDENCE_INTERVALS = (10, 50, 90)
N_FCASTS = 1

assigner = Assigner({
    'Bootstrap': (0, 1),
    'Context': ('both', 'neither', 'second-only')
})
fcast_selector = Randomizer(forecast_questions, r=N_FCASTS)

@route('/survey')
def start():
    conditions = assigner.next()
    fcast_questions = make_fcast_questions()
    intro_page = Page(
        Label(
            '''
            We will now ask you to make some estimates.
            '''
        )
    )
    if current_user.meta['Context'] != 'both':
        intro_page.questions.append(Label(
            '''
            You won't know the context for the estimates you'll be making. You're simply estimating a variable which changes over time.
            '''
        ))
    return Branch(
        intro_page,
        *[
            make_first_estimate_page(content, fcast_inputs)
            for content, fcast_inputs in fcast_questions
        ],
        navigate=N.second_estimates(fcast_questions)
    )

@N.register
def second_estimates(first_estimate_branch, fcast_questions):
    intro_page = Page(
        Label(
            '''
            We will now ask you to make new estimates for all of the questions you just answered. Your second estimate should be different from your first.
            '''
        )
    )
    if current_user.meta['Context'] == 'second-only':
        intro_page.questions.append(Label(
            '''
            When making your second estimates, we will reveal the context. That is, you will know what you are estimating.
            '''
        ))

    return Branch(
        intro_page,
        *[
            make_second_estimate_page(content, fcast_inputs)
            for content, fcast_inputs in fcast_questions
        ],
        completion_page()
    )

def make_fcast_questions():
    fcast_content = fcast_selector.next()
    fcast_content = (
        list(fcast_content) if isinstance(fcast_content, tuple)
        else [fcast_content]
    )
    shuffle(fcast_content)
    current_user.embedded.append(
        Embedded('Forecast', [q['name'] for q in fcast_content])
    )
    return [[content, make_questions(content, first_estimate=True)] for content in fcast_content]

def make_questions(content, first_estimate):
    def make_question(ci, content):
        return Blank(
            (content['question'][0].format(ci), content['question'][1]),
            var=var+str(ci), append=content['append'],
            blank_empty='_____', type='number', required=True
        )

    if (
        (
            first_estimate 
            and current_user.meta['Context'] == 'both'
        )
        or (
            not first_estimate 
            and current_user.meta['Context'] != 'neither'
        )
    ):
        content_ = content['context']
        var = 'FirstEstimate'
    else:
        content_ = content['no_context']
        var = 'SecondEstimate'
    return [make_question(ci, content_) for ci in CONFIDENCE_INTERVALS]

def make_first_estimate_page(content, fcast_inputs):
    content = content.copy()
    content['use_context'] = current_user.meta['Context'] == 'both'
    return Page(
        Dashboard(src='/dashapp/', g=content), 
        *fcast_inputs,
        timer='FirstEstimateTime'
    )

def make_second_estimate_page(content, fcast_inputs):
    def make_reminder(reminder_txt):
        return html_list(
            *[
                (
                    'There is a {} in 100 chance '+reminder_txt
                ).format(ci, fcast_input.response)
                for ci, fcast_input in zip(CONFIDENCE_INTERVALS, fcast_inputs)
            ], 
            ordered=False
        )

    content = content.copy()
    if current_user.meta['Context'] != 'neither':
        content['use_context'] = True
        content_ = content['context']
    else:
        content['use_content'] = False
        content_ = content['no_context']
    if current_user.meta['Bootstrap']:
        additional_questions = [
            Textarea(
                '''
                <p>Imagine your first estimates were off the mark. Write at least one reason why that could be. Which assumptions or considerations could have been wrong?</p>
                ''',
                var='Assumptions', required=True, validate=V.min_words(7)
            ),
            Check(
                '''
                <p>What does this reason imply? Were your first estimate too high or too low?</p>
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
    else:
        additional_questions = [
            Label(
                '''
                Please make second estimates which are different from your first estimates.
                '''
            )
        ]
    return Page(
        Dashboard(src='/dashapp/', g=content),
        Label(
            '''
            <p>Your first estimates were:</p>
            ''' + make_reminder(content_['remind'])
        ),
        *additional_questions,
        *make_questions(content, first_estimate=False),
        timer='SecondEstimateTime'
    )