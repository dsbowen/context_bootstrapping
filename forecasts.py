forecast_questions = [
    dict(
        name='COVID_cases',
        file_name='covid_cases.csv',
        title='Daily new COVID-19 cases in the U.S.',
        context=dict(
            question='<p>How many new COVID-19 cases will be reported in the U.S. in 5 days?</p>',
            append='thousand new cases',
            remind='that there will be {} thousand new COVID-19 cases reported in the U.S. in 5 days',
            x='Date',
            y='New daily cases'
        ),
        no_context=dict(
            question='<p>What will be the value of this line in 5 time steps?</p>',
            append='thousand',
            remind='{} thousand',
            x='Time',
            y='Thousand'
        )
    )
]