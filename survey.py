from forecasts import forecast_questions

from flask_login import current_user
from hemlock import Branch, Page, Embedded, Binary, Dashboard, Input, Textarea, Label, Validate as V, Navigate as N, route
from hemlock.tools import Assigner, Randomizer, consent_page, completion_page

from random import shuffle

N_FCASTS = 1

assigner = Assigner({
    'Bootstrap': (0, 1),
    'Context': ('both', 'neither', 'second-only')
})
fcast_selector = Randomizer(forecast_questions, r=N_FCASTS)

@route('/survey')
def start():
    conditions = assigner.next()
    print(conditions)
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
            make_first_estimate_page(content, fcast_input)
            for content, fcast_input in fcast_questions
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
            make_second_estimate_page(content, fcast_input)
            for content, fcast_input in fcast_questions
        ],
        completion_page()
    )

def make_fcast_questions():
    def make_question(content):
        if current_user.meta['Context'] == 'both':
            content_ = content['context']
        else:
            content_ = content['no_context']
        return Input(
            content_['question'],
            var='FirstEstimate', append=content_['append'],
            type='number', required=True
        )
        
    fcast_content = fcast_selector.next()
    fcast_content = (
        list(fcast_content) if isinstance(fcast_content, tuple)
        else [fcast_content]
    )
    shuffle(fcast_content)
    current_user.embedded.append(
        Embedded('Forecast', [q['name'] for q in fcast_content])
    )
    return [[content, make_question(content)] for content in fcast_content]

def make_first_estimate_page(content, fcast_input):
    content = content.copy()
    content['use_context'] = current_user.meta['Context'] == 'both'
    return Page(
        Dashboard(src='/dashapp/', g=content), 
        fcast_input,
        timer='FirstEstimateTime'
    )

def make_second_estimate_page(content, fcast_input):
    content = content.copy()
    if current_user.meta['Context'] != 'neither':
        content['use_context'] = True
        content_ = content['context']
    else:
        content['use_context'] = False
        content_ = content['no_context']
    if current_user.meta['Bootstrap']:
        additional_questions = [
            Textarea(
                '''
                <p>Imagine your first estimate was off the mark. Write at least one reason why that could be. Which assumptions or considerations could have been wrong?</p>
                '''.format(fcast_input.response),
                var='Assumptions', required=True, validate=V.min_words(7)
            ),
            Binary(
                '''
                <p>What does this reason imply? Was your first estimate too high or too low?</p>
                ''',
                ['Too high', 'Too low'],
                var='TooHigh', validate=V.require()
            ),
            Label(
                '''
                Based on this new perspective, make a second estimate which is different from the first.
                '''
            )
        ]
    else:
        additional_questions = [
            Label(
                '''
                Please make a second estimate which is different from the first.
                '''
            )
        ]
    return Page(
        Dashboard(src='/dashapp/', g=content),
        Label(
            '''
            Your first estimate was {}.
            '''.format(content_['remind'].format(fcast_input.response))
        ),
        *additional_questions,
        Input(
            content_['question'],
            var='SecondEstimate', append=content_['append'],
            type='number', required=True
        ),
        timer='SecondEstimateTime'
    )