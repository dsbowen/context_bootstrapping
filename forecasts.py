from hemlock import Blank

# number of time steps ahead that participants are forecasting
TIME_STEPS = 5
CONTEXT = (
    '<p>There is a {pctile} in 100 chance that there will be {fewer_less} than ',
    ' {y} {t} {t_units} after the end of this graph'
)

def make_question(pctile, context, var):
    y_scale = context.get('y_scale')
    y_scale = '' if y_scale is None else y_scale + ' ' 
    y = context.get('y_variable')
    if y is None:
        y = context['y']
        y = y[0].lower() + y[1:]
    t_units = context.get('t_units') or context['x']
    return Blank(
        (
            CONTEXT[0].format(
                pctile=pctile,
                fewer_less=context['fewer_less']
            ),
            CONTEXT[1].format(
                y=y_scale+y,
                t=TIME_STEPS,
                t_units=t_units
            )
        ),
        var=var+str(pctile), append=t_units, step='any', type='number',
        blank_empty='_____',  required=True
    )

forecast_questions = [
    dict(
        name='COVID_cases',
        filename='covid_cases.csv',
        y_scale='thousand',
        y_variable='new COVID-19 cases reported in the U.S.',
        t_units='days',
        title='Daily new COVID-19 case in the U.S.',
        x='Date',
        y='New daily cases'
    ),
    dict(
        name='Tsunamis',
        filename='tsunamis.csv',
        t_units='years',
        y_variable='annual tsunamis',
        title='Annual tsunamis',
        x='Year',
        y='Annual tsunamis'
    )
]

forecast_questions = [
    dict(
        name='COVID_cases',
        filename='covid_cases.csv',
        title='Daily new COVID-19 cases in the U.S.',
        time_steps=5,
        context=dict(
            question=('<p>There is a {} in 100 chance that there will be fewer than ', ' thousand new COVID-19 cases reported in the U.S. {} days after the end of this graph</p>'),
            append='thousand new cases',
            remind='that there will be {} thousand new COVID-19 cases reported in the U.S. {} days after the end of this graph',
            x='Date',
            y='New daily cases'
        ),
        no_context=dict(
            question=('<p>There is a {} in 100 chance that the line will be below ', ' {} time steps after the end of this graph</p>'),
            append='thousand units',
            remind='that the line will be below {} thousand {} time steps after the end of this graph',
            x='Time',
            y='Thousand'
        )
    ),
    dict(
        name='Tsunamis',
        filename='tsunamis.csv',
        title='Annual Tsunamis',
        time_steps=5,
        context=dict(
            question=('<p>There is a {} in 100 chance that there will be fewer than ', ' annual tsunamis {} years after the end of this graph'),
            append='annual tsunamis',
            remind='that there will be {} annual tsunamis {} years after the end of this graph',
            x='Year',
            y='Annual tsunamis'
        ),
        no_context=dict(
            question=('<p>There is a {} in 100 chance that the line will be below ', ' {} time steps after the end of this graph</p>'),
            append='units',
            remind='that the line will be below {} {} time steps after the end of this graph',
            x='Time',
            y='Units'
        )
    )
]