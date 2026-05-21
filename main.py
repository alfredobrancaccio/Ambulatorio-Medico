import sys
from app_db import AmbulatorioDatabase


def main():
    args  = sys.argv[1:]
    reset = "--reset" in args
    web   = "--web" in args

    db = AmbulatorioDatabase()
    db.initialize(reset=reset)

    if web:
        from app_web import app
        app.run(debug=True)
    else:
        from app_repl import AmbulatorioREPL
        AmbulatorioREPL(db).esegui()


main()
