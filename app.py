import eventlet
eventlet.monkey_patch()

import survey
from display import make_dashboard

from hemlock import create_app

app = create_app()
make_dashboard(app)

if __name__ == '__main__':
    from hemlock.app import socketio
    socketio.run(app, debug=True)