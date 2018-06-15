#!/usr/bin/python

from flask import request, send_file, render_template, flash, url_for, redirect, Blueprint

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
        """The last 13 guys? They didn't have what it takes.
         But you? YOU'VE got the stuff.""",
        "Intelligence 8? This character is just like you!",
        "Old age looked boring anyway"]

ERROR_MESSAGES = {
    'TYPE': "Put some NUMBERS in there, you degenerate.",
    'LURVS': """I love you with all my heart, Moxxi.
     Even in code. Forever and always.""",
    'NEGATIVE': """Really. You'd like NEGATIVE %s characters.
     Uh huh. Lemme get right on that.""",
    'ZERO': """There you go! I generated NO characters for you,
      just like you asked."""}

lamentApp = Blueprint('lament', __name__)


@lamentApp.route('/character')
def index():
    return render_template('lament/lament.html', sass=random.choice(SASS))


@lamentApp.route('/lament', methods=['GET', 'POST'])
def lament_pdf():
    path_to_pdftk = tools.get_pdftk_path()
    tmpdir = tempfile.TemporaryDirectory(dir=os.path.dirname(__file__))
    calculate_encumbrance = True

    if "desired_class" in request.form.keys():
        desired_class = request.form['desired_class']
        number = 1
    else:
        number = request.form['randos']
        desired_class = None
        try:
            number = int(number)
        except (TypeError, ValueError):
            message = ERROR_MESSAGES['TYPE']
            if number in ('lurvs', 'Lurvs'):
                message = ERROR_MESSAGES['LURVS']
            flash(message)
            return redirect(url_for('lament.index'))

        if number <= 0:
            if number < 0:
                message = ERROR_MESSAGES['NEGATIVE'] % abs(number)
            else:
                message = ERROR_MESSAGES['ZERO']
            flash(message)
            return redirect(url_for('lament.index'))

    if number > 20:
        number = 1

    for i in range(number):
        if desired_class:
            PC = character.LotFPCharacter(
                desired_class,
                calculate_encumbrance=calculate_encumbrance,
                counter=i)
        else:
            PC = character.LotFPCharacter(
                calculate_encumbrance=calculate_encumbrance,
                counter=i)

        # If the character has spells, create a PDF spell sheet and fill
        # it with spells and spell info
        if PC.pcClass in ['Cleric', 'Magic-User', 'Elf']:
            tools.create_spellsheet_pdf(
                PC.details,
                PC.name,
                filename=None,
                directory=tmpdir.name)

        # Create fdf data files to fill PDF form fields
        fdf_data = forge_fdf("", PC.details, [], [], [])
        with open(os.path.join(tmpdir.name, PC.fdf_name), 'wb') as f:
            f.write(fdf_data)

        # All of the command-line arguments for PDFtk,
        # since they were getting kinda long.
        args = [path_to_pdftk,
                os.path.join(
                    os.path.dirname(__file__),
                    'LotFPCharacterSheetLastGaspFillable.pdf'),
                'fill_form',
                PC.fdf_name,
                'output',
                PC.filled_name,
                'flatten']

        # Fill the forms with PDFtk, store them in the tempfiles directory.
        subprocess.run(args, cwd=tmpdir.name, **tools.subprocess_args(False))

    if desired_class:
        final_name = os.path.join('FinalPDF', desired_class + '.pdf')
    else:
        final_name = os.path.join('FinalPDF', str(number) + 'Characters.pdf')

    try:
        os.mkdir('FinalPDF')
    except FileExistsError:
        pass

    # Remove any conflicting final PDFs.
    if os.path.exists(final_name):
        os.remove(final_name)

    subprocess.run([path_to_pdftk,
                    os.path.join(tmpdir.name, '*.pdf'),
                    'cat',
                    'output',
                    final_name],
                   **tools.subprocess_args(False))

    return send_file(final_name,
                     mimetype="application/pdf",
                     as_attachment=True,
                     attachment_filename=final_name)
