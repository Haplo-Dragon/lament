#!/usr/bin/python

from flask import request, send_file, render_template, flash, url_for, redirect, Flask

import character
import tools
from fdfgen import forge_fdf
import subprocess
import os
import tempfile
import random

SASS = ["All these guys are gonna die anyway",
        "A 1 is good, right?",
        "HOW many hit points?",
        "No, I'm sure those spells will be useful",
        "Don't get too attached",
        "The last 13 guys? They didn't have what it takes. But you? YOU'VE got the stuff.",
        "Intelligence 8? This character is just like you!",
        "Old age looked boring anyway"]

DEBUG = True
app = Flask(__name__)


def main():
    app.config.from_object(__name__)
    app.DEBUG = True
    app.secret_key = 'Top secret lurvs for the Moxxi'
    app.run("0.0.0.0")


@app.route('/')
def interface():
    return redirect(url_for('index'))


@app.route('/index')
def index():
    return render_template('lament.html', sass=random.choice(SASS))


@app.route('/lament/', methods=['GET', 'POST'])
def lament(desired_class=None, number=1, calculate_encumbrance=True):
    path_to_pdftk = tools.get_pdftk_path()
    tmpdir = tempfile.TemporaryDirectory(dir=os.getcwd())

    if request.method == 'GET':
        return redirect(url_for('index'))

    if request.method == 'POST':
        if "desired_class" in request.form.keys():
            desired_class = request.form['desired_class']
        if "randos" in request.form.keys():
            try:
                number = int(request.form['randos'])
            except TypeError:
                flash("%s? Really?!" % number)
                return redirect(url_for('index'))
            except ValueError:
                flash("Put some NUMBERS in there, you degenerate.")
                return redirect(url_for('index'))

            if number <= 0:
                flash("Really. You'd like NEGATIVE %s characters. Uh huh. Lemme get right on that." % abs(number))
                return redirect(url_for('index'))

    if number > 25:
        flash("REALLY? %s? You're getting 25, meatbag." % number)
        number = 25

    for i in range(number):
        if desired_class:
            PC = character.LotFPCharacter(desired_class,
                                          calculate_encumbrance=calculate_encumbrance,
                                          counter=i)
        else:
            PC = character.LotFPCharacter(calculate_encumbrance=calculate_encumbrance,
                                          counter=i)

        percentage = int(100 * (i - 1) / number)

        # If the character has spells, create a PDF spell sheet and fill it with spells and spell info
        if PC.pcClass in ['Cleric', 'Magic-User', 'Elf']:
            tools.create_spellsheet_pdf(PC.details, PC.name, filename=None, directory=tmpdir.name)

        # Create fdf data files to fill PDF form fields
        fdf_data = forge_fdf("", PC.details, [], [], [])
        with open(tmpdir.name + "\\" + PC.fdf_name, 'wb') as f:
            f.write(fdf_data)

        # All of the command-line arguments for PDFtk, since they were getting kinda long.
        args = [path_to_pdftk,
                '..\LotFPCharacterSheetLastGaspFillable.pdf',
                'fill_form',
                PC.fdf_name,
                'output',
                PC.filled_name,
                'flatten']

        # Fill the forms with PDFtk, store them in the tempfiles directory.
        subprocess.run(args, cwd=tmpdir.name, **tools.subprocess_args(False))

    if desired_class:
        final_name = 'FinalPDF\\' + desired_class + '.pdf'
    else:
        final_name = 'FinalPDF\\' + str(number) + 'Characters.pdf'

    try:
        os.mkdir('FinalPDF')
    except FileExistsError:
        pass

    # Remove any conflicting final PDFs.
    if os.path.exists(final_name):
        os.remove(final_name)

    subprocess.run([path_to_pdftk, tmpdir.name + '\*.pdf', 'cat', 'output', final_name],
                   **tools.subprocess_args(False))

    return send_file(final_name, mimetype="application/pdf", as_attachment=True)

"""
@app.route('/progress')
def progress(message="", value=10):
    return render_template('progress.html', value=value, message=message)
"""

if __name__ == "__main__":
    main()
