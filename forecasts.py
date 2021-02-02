forecast_questions = [
    dict(
        name='COVID_cases',
        file_name='covid_cases.csv',
        title='Daily new COVID-19 cases in the U.S.',
        context=dict(
            question=('<p>There is a {} in 100 chance that there will be fewer than ', ' new COVID-19 cases reported in the U.S. in 5 days</p>'),
            append='thousand new cases',
            remind='that there will be {} thousand new COVID-19 cases reported in the U.S. in 5 days',
            x='Date',
            y='New daily cases'
        ),
        no_context=dict(
            question=('<p>There is a {} in 100 chance that the line will be below ', ' in 5 time steps</p>'),
            append='thousand',
            remind='that the line will be below {} thousand in 5 time steps',
            x='Time',
            y='Thousand'
        )
    )
]