import PySimpleGUI as sg  # Not default library
import sys
import json
import GradingGUI_library as guilib

# V0.1.1 added constraints to mistake calculations + fixed issues when student not chosen.
# V0.2.1 added excluded errors.
# V0.2.2 Added update all error points function
# V0.2.3 Moving functions to library file to save space.
# V0.2.4 Moving rest of the functions to GradingGUI_library.py file
# V0.2.5 Fixed bug with summing to existing value or substracting from it
# V0.2.6 Removed pylint warnings.
# V0.3.0 New dependency pyperclip and added ability to copy moodle text straight from UI.
# V0.3.1 Fixed bug with copy function.
# V0.3.2 Fixed another bug with copy function and changed file path split to fix problems.
# V0.3.3 Fixed first category not copying properly.
# V0.3.4 Added constants for font and rows amount and updated copied text.
# V0.3.5 Changed error values to not fail student if student is not over threshold
# V0.3.6 Added error comment texts
# V0.3.7 Added suggested grades
# V0.3.8 Fixed all wrong (-1 selection) severities to work with floats
#        and fixed text generation of category status to work with in progress
#        ("Kesken") status also in other but last category
# V0.3.9 Added MINIMUM_LEVEL boolean constant to update FAIL_LIMIT to 1, if True


FONT_SIZE = 11  # Font size, default is 11
PROBLEM_LIST_ROWS = 15  # How many rows are shown to user, default is 15.
L08T5 = False  # For L08-T5 checking.
REATTEMPT = False  # For "Korjauspalautus" change to True.
MINIMUM_LEVEL = True  # For checking submissions from minimum level.


FAIL_LIMIT = 2
FAIL_TEXT = "Harjoitustyön Palautus on korjattava."
PASS_TEXT = "Harjoitustyön Palautus on hyväksytty."
MAX_GRADES = {
            "minimi" : 1,
            "perus": 3,
            "tavoite" : 5
}

if REATTEMPT:
    MAX_GRADES["minimi"] = 1
    MAX_GRADES["perus"] = 2
    MAX_GRADES["tavoite"] = 4

if L08T5:
    FAIL_LIMIT = 1
    FAIL_TEXT = 'L08T5 ohjelman rakenne "ei ole annettujen ohjeiden mukainen".'
    PASS_TEXT = 'L08T5 ohjelman rakenne "on kunnossa".'

if MINIMUM_LEVEL:
    FAIL_LIMIT = 1

sg.theme("BlueMono")
font = ("Arial", FONT_SIZE)
treedata = sg.TreeData()

starting_path = sg.popup_get_folder("Anna näytettävä kansio")


if not starting_path:
    sys.exit(0)

### Create Tree Structure for problems ###
studentdata = sg.TreeData()
###Create menu for MenuBar ###
menu_def = [
    [
        "Toiminto",
        ["Export opiskelijadata", "Laske virhepisteet", "Päivitä virhepisteet"],
    ]
]

treecol = [
    [
        sg.Tree(
            data=studentdata,
            headings=[],
            auto_size_columns=True,
            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
            num_rows=7,
            col0_width=27,
            key="-PROGRAMS-",
            show_expanded=False,
            pad=(2, 2),
            enable_events=True,
            expand_x=False,
            expand_y=True,
            row_height=30,
        ),
        sg.Multiline(
            key="virheteksti",
            default_text="Laita tähän virhekoodia.",
            horizontal_scroll=True,
            autoscroll=True,
            size=(25, 10),
        ),
        sg.Multiline(
            key="-ERROROUT-",
            expand_x=True,
            autoscroll=True,
            horizontal_scroll=True,
            size=(25, 10),
            tooltip="Syötetty koodi näkyy tässä laatikossa.",
        ),
    ],
    [
        sg.Tree(
            data=treedata,
            headings=["lkm"],
            auto_size_columns=False,
            select_mode=sg.TABLE_SELECT_MODE_EXTENDED,
            num_rows=PROBLEM_LIST_ROWS,
            col0_heading="Ongelmat koodissa",
            col0_width=56,
            col_widths=2,
            key="-TREE-",
            show_expanded=False,
            enable_events=True,
            expand_x=False,
            expand_y=True,
        )
    ],
    [
        sg.Button("Tallenna", key="SAVE"),
        sg.Button("Kirjoita arvostellut työt tiedostoon", key="WRITE"),
        sg.Button("Kopioi teksti leikepöydälle", key="-COPY-"),
        sg.Button("Exit"),
    ],
]

buttoncol = [
    [
        sg.Button("+", key="+"),
        sg.Button("-", key="-"),
    ],
    [sg.Button("Ei yhtään oikein", key="ALL")],
    [sg.Text("Virhepisteet ovat:"), sg.Txt(key="-virheout-", text=0)],
    [sg.Text("Arvosanat:")],
    [sg.Text("Minimitaso:"), sg.Txt(key="-arvosana_minimi-", text=MAX_GRADES["minimi"])],
    [sg.Text("Perustaso:"), sg.Txt(key="-arvosana_perus-", text=MAX_GRADES["perus"])],
    [sg.Text("Tavoitetaso:"), sg.Txt(key="-arvosana_tavoite-", text=MAX_GRADES["tavoite"])],
]

### Layout for GUI ####
layout = [
    [
        sg.MenuBar(menu_def, tearoff=False),
        sg.Text("Opiskelijat"),
        sg.Text("         " * 5),
        sg.Text("Laita virheen koodi alle."),
        sg.Text("   "),
        sg.pin(sg.Button("<-", enable_events=True, key="-LEFT-")),
        sg.Text("     " * 3),
        sg.Button("->", enable_events=True, key="-RIGHT-"),
    ],
    [sg.Column(treecol, expand_y=False), sg.Column(buttoncol, expand_x=True)],
]
#################################################################################################


def main():
    errorlist = {}
    virheen_lukumaara = 0
    students = {}
    errorpoints = 0
    category_sum = 0
    index = 0
    virhekoodi = []
    printlist = []
    feedbacklist = []
    guilib.add_files_in_folder("", starting_path, studentdata)
    baseinfo, category_list = guilib.initiate_problem_list(
        treedata
    )  # WIP: Tee opiskelijakohtainen kopio category_list:istä
    students = guilib.read_json_update_students(students)
    window = sg.Window("Grading tool", layout, resizable=True, font=font, finalize=True)
    tree = window["-PROGRAMS-"]  # type: sg.Tree
    tree.bind("<Double-1>", "+DOUBLE")

    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED:
            break

        ### Adding to problem counter ###
        if event == "+" or event == "-":
            if event == "+":
                try:
                    selected_mistake = values["-TREE-"][0]
                    if selected_mistake in errorlist.keys():
                        errorlist[selected_mistake] += 1
                    else:
                        if "path2" in locals():
                            if selected_mistake not in students[path2]:
                                virheen_lukumaara = 1
                                errorlist[selected_mistake] = virheen_lukumaara
                    try:
                        window["-TREE-"].update(
                            key=selected_mistake, value=errorlist[selected_mistake]
                        )
                    except KeyError:
                        print("Valitse opiskelija ensin.")
                    if students:
                        if "path2" in locals():
                            for student in students:
                                if (
                                    selected_mistake in students[student]
                                    and student == path2
                                ):
                                    if students[student][selected_mistake] > 0:
                                        students[student][selected_mistake] += 1
                                        window["-TREE-"].update(
                                            key=selected_mistake,
                                            value=students[student][selected_mistake],
                                        )
                except IndexError:
                    print("Listalla ei ole vielä opiskelijaa.")
                    continue

            ### Decreasing problem counter ###
            if event == "-":
                if students:
                    selected_mistake = values["-TREE-"][0]
                    if "path2" in locals():
                        for student in students:
                            if (
                                selected_mistake in students[student]
                                and student == path2
                            ):
                                if students[student][selected_mistake] > 0:
                                    students[student][selected_mistake] -= 1
                                    window["-TREE-"].update(
                                        key=selected_mistake,
                                        value=students[student][selected_mistake],
                                    )
                if selected_mistake in errorlist:
                    if errorlist[selected_mistake] > 0:
                        if selected_mistake in errorlist.keys():
                            errorlist[selected_mistake] -= 1
                    else:
                        virheen_lukumaara = 0
                        errorlist[selected_mistake] = virheen_lukumaara
                    window["-TREE-"].update(
                        key=selected_mistake, value=errorlist[selected_mistake]
                    )

        ### If all occurances are wrong ###
        if event == "ALL":
            window["-TREE-"].update(key=values["-TREE-"][0], value=-1)
            errorlist[
                values["-TREE-"][0]
            ] = -1  ## -1 is easy repsesentation for all being wrong
        ### If row is selected change student that is updated ###

        if event == "-PROGRAMS-":
            printlist.clear()
            feedbacklist.clear()
            selected_student = values["-PROGRAMS-"][0]
            category_texts = [
                "toiminnallisuus tehtäväksiannon mukaan ja CodeGradesta läpi",
                "tiedostorakenne useita tiedostoja",
                "ohjeiden mukaiset alkukommentit",
                "ohjelmarakenne pääohjelma ja aliohjelmat",
                "perusoperaatiot tulostus, syöte, valintarakenne, toistorakenne",
                "tiedonvälitys parametrit ja paluuarvot, ei globaaleja muuttujia",
                "tiedostonkäsittely luku ja kirjoittaminen",
                "tietorakenteet lista, luokka ja olio",
                "poikkeustenkäsittely tiedostonkäsittelyssä",
                "analyysien toteutus",
                "toteutuksen selkeys, ymmärrettävä, ylläpidettävä ja laajennettava",
            ]
            k = guilib.key_define(tree)
            path2 = guilib.update_fields(
                selected_student, students, window, errorlist, k, studentdata, treedata, MAX_GRADES, FAIL_LIMIT
            )
            print("PATH2 update fieldsin jälkeen", path2)
            window["virheteksti"].update(value="")
            kategoria = ""
            # Initiate category_list so that status is OK before counting category_sums
            for i in category_list:
                i.status = "OK"

            ### Lets make sure that all the category amounts are zero
            category_sum = guilib.clear_sums(window, baseinfo, treedata)

            ### Counting category sums ###

            selected_student = students[path2]
            if selected_student != []:
                for error in baseinfo:
                    if error.error in selected_student.keys():
                        if selected_student[error.error] == 0:
                            del selected_student[error.error]
                            continue
                        feedbacklist.append(error.feedback)
                        node = treedata.tree_dict[error.error]
                        parent_node = treedata.tree_dict[node.parent]
                        if parent_node.parent == "":
                            if kategoria != parent_node.text and kategoria != "":
                                window["-TREE-"].update(
                                    key=kategoria, value=category_sum
                                )
                                for i in category_list:
                                    if kategoria == i.category:
                                        i.category_sum = category_sum
                                        if (
                                            category_sum > 0
                                            and "virhepisteet" in selected_student
                                            and selected_student["virhepisteet"]
                                            >= FAIL_LIMIT
                                        ):
                                            i.status = "EiOK"
                                        elif (
                                            not L08T5
                                            and category_sum > 0
                                            and "virhepisteet" in selected_student
                                            and selected_student["virhepisteet"] < FAIL_LIMIT
                                        ):
                                            i.status = "Kesken"
                                category_sum = 0
                            kategoria = parent_node.text
                            category_sum = category_sum + abs(
                                selected_student[error.error]
                            )
                window["-TREE-"].update(key=kategoria, value=category_sum)
                for i in category_list:
                    if kategoria == i.category:
                        i.category_sum = category_sum
                        if (
                            category_sum > 0
                            and "virhepisteet" in selected_student
                            and selected_student["virhepisteet"] >= FAIL_LIMIT
                        ):
                            i.status = "EiOK"
                        elif (
                            not L08T5
                            and category_sum > 0
                            and "virhepisteet" in selected_student
                            and selected_student["virhepisteet"] < FAIL_LIMIT
                        ):
                            i.status = "Kesken"
            counter = 0
            printlist.append("Tarkempi arviointi:")
            for i in category_list:
                counter += 1
                if L08T5 and counter == 9:
                    printlist.append(
                        str(counter)
                        + ". "
                        + category_texts[counter - 1]
                        + ": - ei arvioida L08-tehtävässä"
                    )

                else:
                    printlist.append(
                        str(counter)
                        + ". "
                        + category_texts[counter - 1]
                        + ": "
                        + i.status
                    )
            if (
                "virhepisteet" in selected_student
                and selected_student["virhepisteet"] >= FAIL_LIMIT
            ):
                printlist.insert(0, FAIL_TEXT)

            else:
                printlist.insert(0, PASS_TEXT)

            for printtaus in printlist:
                print(printtaus)
            printlist.append("\nKommentit:")
            for feedback in feedbacklist:
                printlist.append(feedback)

            index = 0

        ###Adding checkboxes next to student names for easier marking ###
        if event.endswith("DOUBLE"):
            guilib.double_click(tree, studentdata)


        ### Save added rows to other tree structure ###
        if event == "SAVE":
            try:
                error_text = values["virheteksti"]
                if errorlist != {} and path2 not in students:
                    guilib.mergedicts(errorlist, students, path2)
                if error_text == "Laita tähän virhekoodia.":
                    error_text = ""
                elif "virhekoodi" in students[path2]:
                    if error_text != "":
                        students[path2]["virhekoodi"].append(error_text)
                    guilib.mergedicts(errorlist, students, path2)
                else:
                    if error_text != "":
                        virhekoodi.append(error_text)
                        # Adding copy of a list so program does not override existing value due referencing
                        errorlist["virhekoodi"] = virhekoodi.copy()
                        guilib.mergedicts(errorlist, students, path2)
                        virhekoodi.clear()

                    else:
                        guilib.mergedicts(errorlist, students, path2)

                window["virheteksti"].update(value="")
            except UnboundLocalError:
                sg.popup_ok("Valitse opiskelija ja yritä uudelleen")
                print("Valitse opiskelija ja yritä uudelleen")
            #####################Counting mistake points ##############################
            alternative_added = False
            try:
                kategoria = ""
                category_sum = guilib.clear_sums(window, baseinfo, treedata)
                selected_student = students[path2]
                guilib.remove_excludes(
                    selected_student, baseinfo
                )  # Remove excluded error from list if found
                print(selected_student)
                for error in baseinfo:

                    if selected_student != []:
                        if error.error in selected_student.keys():
                            biggest = 0

                            node = treedata.tree_dict[error.error]
                            parent_node = treedata.tree_dict[node.parent]

                            if parent_node.parent == "":

                                if kategoria != parent_node.text and kategoria != "":
                                    print("KATEGORIA ON", kategoria, parent_node.text)
                                    window["-TREE-"].update(
                                        key=kategoria, value=category_sum
                                    )
                                    category_sum = 0
                                kategoria = parent_node.text
                                category_sum = category_sum + abs(
                                    selected_student[error.error]
                                )
                                window["-TREE-"].update(
                                    key=kategoria, value=category_sum
                                )
                            (
                                errorpoints,
                                alternative_added,
                            ) = guilib.count_alternative_points(
                                error,
                                baseinfo,
                                selected_student,
                                alternative_added,
                                errorpoints,
                            )
                            for i in error.amount:
                                if i == "All" and selected_student[error.error] == -1:
                                    errorpoints = errorpoints + float(error.severity[i])
                                    break
                                elif i == "All" or i == "virhekoodi":
                                    continue

                                if int(i) <= selected_student[error.error]:
                                    biggest = i

                            if (
                                selected_student[error.error] != -1
                                and alternative_added == False
                                and biggest != 0
                            ):
                                errorpoints = errorpoints + float(
                                    error.severity[str(biggest)]
                                )

                            print("Virheen pisteet ovat :", round(errorpoints, 1))
                            alternative_added = False

                errorpoints = round(errorpoints, 1)
                selected_student["virhepisteet"] = errorpoints
                window["-virheout-"].update(errorpoints)
                guilib.update_grades(window, errorpoints, MAX_GRADES, FAIL_LIMIT )
                print(selected_student)

            except UnboundLocalError as e:
                print("Valitse Opiskelija ensin.", e)
            # Lets clear the variable for new mistake points
            errorpoints = 0

        if event == "-RIGHT-":
            index = index + 1
            try:
                if "path2" in locals():
                    if path2 in students:
                        if "virhekoodi" in students[path2]:
                            print(students[path2]["virhekoodi"])
                            window["-ERROROUT-"].update(
                                students[path2]["virhekoodi"][index]
                            )
                            window["-LEFT-"].update(visible=True)
            except IndexError:
                print("List end add more error code.")
                index = index - 1

        if event == "-LEFT-":
            if "path2" not in locals():
                continue
            if "virhekoodi" in students[path2]:
                if values["-ERROROUT-"] != students[path2]["virhekoodi"][0]:
                    index = index - 1
                    window["-ERROROUT-"].update(students[path2]["virhekoodi"][index])
                    window["-RIGHT-"].update(visible=True)
        if event == "WRITE":
            try:
                with open("Arvostellut.json", "w", encoding="utf-8") as outfile:
                    json.dump(students, outfile, indent=4, ensure_ascii=False)
            except Exception as e:
                print("File opening failed with error code:", e)
        if event == "Päivitä virhepisteet":
            guilib.update_error_points(window, baseinfo, students, treedata, MAX_GRADES, FAIL_LIMIT)
            # WIP:Vaihda for looppiin joka päivittää students dictissä olevat virhepisteet nyt uusiin laskettuihin.

        if event == "-COPY-":

            guilib.list_to_clipboard(printlist)


main()
