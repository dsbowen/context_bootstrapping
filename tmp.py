from hemlock import Branch, Page, Label, route

from flask_login import current_user

@route('/survey')
def start():
    current_user.g['tmp'] = [Label() for _ in range(3*9)]
    return Branch(
        *[
            Page(
                *[
                    Label(' '.join([str(i) for i in range(10)]))
                    for _ in range(10)
                ]
            ) 
            for _ in range(10)
        ],
        Page(
            Label(
                'The end'
            ),
            terminal=True
        )
    )