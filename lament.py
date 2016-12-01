#!/usr/bin/python

import character
import tools
from fdfgen import forge_fdf
import subprocess
import os
import tempfile
import GUI
import wx
from wx.lib.pubsub import pub

"""
choice = None
classes = ['Fighter', 'Magic-User', 'Specialist', 'Cleric', 'Dwarf', 'Elf', 'Halfling']
menu = {
    '1.': "Random characters",
    '2.': "Specific class"
}

while True:
    options = sorted(menu.keys())
    print("Would you like to generate random characters, or a specific class?")
    for entry in options:
        print(entry, menu[entry])
    try:
        choice = int(input("\nChoice: "))
        break
    except ValueError:
        print("That wasn't one of the choices! C'mon, it's not that hard. Stupid skintube.\n")

if choice == 2:
    while True:
        try:
            for entry in classes:
                print(entry)
            desired_class = input("Which class would you like to generate?\n>")
            if desired_class not in classes:
                raise ValueError
            break
        except ValueError:
            print("That wasn't one of the classes I offered! Ugh. Primates.\n")
else:
    while True:
        try:
            number = int(input("How many Lamentations of the Flame Princess characters would you like to generate?\n>"))
            break
        except ValueError:
            print("That wasn't an integer. What the hell am I supposed to do with that?\n")
"""


def main():
    app = wx.App()
    print("App created.")
    GUI.LamentFrame(None)
    print("Frame created.")

    pub.subscribe(lament, "specific.generate")
    pub.subscribe(lament, "random.generate")
    print("Subscriptions!")

    app.MainLoop()


def lament(desired_class=None, number=1):
    # number = 1
    # desired_class = None

    tmpdir = tempfile.TemporaryDirectory(dir=os.getcwd())

    if number > 25:
        # print("Really? %s? You're getting 25, meatbag.\n" % number)
        pub.sendMessage("dialog", title="Really?", msg="%s? You're getting 25, meatbag." % number)
        number = 25

    for i in range(number):
        if desired_class:
            PC = character.LotFPCharacter(desired_class, counter=i)
        else:
            PC = character.LotFPCharacter(counter=i)

        percentage = int(100 * (i - 1) / number)
        pub.sendMessage("progress.update", msg="Generating %s of %s" % (i, number),
                        value=percentage)

        # If the character has spells, create a PDF spell sheet and fill it with spells and spell info
        if PC.pcClass in ['Cleric', 'Magic-User', 'Elf']:
            # print("Character has spells - generating spell sheet...")
            pub.sendMessage("progress.update", msg="Character has spells - generating spell sheet...",
                            value=percentage + .5)
            tools.create_spellsheet_pdf(PC.details, PC.name, filename=None, directory=tmpdir.name)

        # Create fdf data files to fill PDF form fields
        fdf_data = forge_fdf("", PC.details, [], [], [])
        with open(tmpdir.name + "\\" + PC.fdf_name, 'wb') as f:
            f.write(fdf_data)

        # All of the command-line arguments for PDFtk, since they were getting kinda long.
        args = ['pdftk',
                '..\LotFPCharacterSheetLastGaspFillable.pdf',
                'fill_form',
                PC.fdf_name,
                'output',
                PC.filled_name,
                'flatten']

        # Fill the forms with PDFtk, store them in the tempfiles directory.
        # print("Creating temporary individual filled PDF for ", PC.name)
        pub.sendMessage("status.update", msg="Creating temporary individual filled PDF for %s..." % PC.name)
        subprocess.run(args, cwd=tmpdir.name)

    try:
        os.mkdir('FinalPDF')
    except FileExistsError:
        pass
    # Remove any conflicting final PDFs.
    if os.path.exists('FinalPDF\\' + str(number) + 'Characters.pdf'):
        os.remove('FinalPDF\\' + str(number) + 'Characters.pdf')

    # print('Creating ', 'FinalPDF\\' + str(number) + 'Characters.pdf', '...')
    pub.sendMessage("progress.update", msg='Creating ' + 'FinalPDF\\' + str(number) + 'Characters.pdf...', value=99)
    pub.sendMessage("status.update", msg='Creating ' + 'FinalPDF\\' + str(number) + 'Characters.pdf...')

    subprocess.run(['pdftk', tmpdir.name + '\*.pdf', 'cat', 'output', 'FinalPDF\\' + str(number) + 'Characters.pdf'])
    # print("\nBoom. %s characters, one PDF. Ready to print. You're welcome." % str(number))
    # print("\nP.S. Don't forget the final PDF is A4.")
    #pub.sendMessage("dialog", title="Done at last!", msg="Boom. %s characters, one PDF. Ready to print. You're welcome."
    #                                                     "\n\nP.S. Don't forget the final PDF is A4." % str(number))


if __name__ == "__main__":
    main()
