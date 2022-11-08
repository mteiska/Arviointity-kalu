
import os
import json
from io import BytesIO
from PIL import Image, ImageDraw
import pyperclip


class Virhetiedot:
    error = "",
    severity = 0
    amount = 0
    alternative = []
    exclude = []

class Category:
    category = ""
    category_sum = 0
    status = "OK"
    
    
def add_files_in_folder(parent, dirname,studentdata):
    files = os.listdir(dirname)
    for f in files:
        fullname = os.path.join(dirname, f).replace("\\","/")
        if os.path.isdir(fullname):            # if folder, add folder and recurse
            studentdata.Insert(parent, fullname, f, values=[0], icon = check[0])
            add_files_in_folder(fullname, fullname,studentdata)
        else:
            studentdata.Insert(parent, fullname, f, values=[0], icon = check[0])

def initiate_problem_list(treedata):
    lista = []
    category_list = []
    f = open('Problem_list.json', encoding = 'utf-8')
    virheet = json.load(f)
    category = virheet['violations'][0]['category']
    treedata.Insert("", 'Toiminnallisuus', 'Toiminnallisuus',
        [0])
    c = Category()
    c.category = category
    c.category_sum = 0
    c.status = "OK"
    category_list.append(c)

    for i in virheet['violations']:
        if category != i['category']:
            treedata.Insert("", i['category'], i['category'],[0])
            treedata.Insert(i['category'], i['ID'], i['text'], [0])
            v = Virhetiedot()
            v.error = i['ID']
            v.severity = i['error_values']
            v.amount = i['error_values'].keys()
            c = Category()
            c.category = i['category']
            c.category_sum = 0
            c.status = "OK"
            category_list.append(c)
            if 'alternatives' in i:
                v.alternative = i['alternatives']
            if 'exclude' in i:
                v.exclude = i['exclude']
            lista.append(v)
            category = i['category']
        else:
            treedata.Insert(i['category'], i['ID'], i['text'], [0])
            v = Virhetiedot()
            v.error = i['ID']
            v.severity = i['error_values']
            v.amount = i['error_values'].keys()
            if 'alternatives' in i:
                v.alternative = i['alternatives']
            if 'exclude' in i:
                v.exclude = i['exclude']
            lista.append(v)
            
    return lista, category_list
    
### Nice to have function for finding selected elements key ###
def key_define(tree):
    item =  tree.Widget.selection()
    return '' if len(item) == 0 else tree.IdToKey[item[0]]

###############################################################
def double_click(tree, studentdata):
    item = tree.Widget.selection()[0]
    key = tree.IdToKey[item]
    index = studentdata.tree_dict[key].values[0]
    index = (index + 1) % 2
    studentdata.tree_dict[key].values[-1] = index
    tree.update(key=key, icon=check[index])

def icon(check):
    box = (32, 32)
    background = (255, 255, 255, 0)
    rectangle = (3, 3, 29, 29)
    line = ((9, 17), (15, 23), (23, 9))
    im = Image.new('RGBA', box, background)
    draw = ImageDraw.Draw(im, 'RGBA')
    draw.rectangle(rectangle, outline='black', width=3)
    if check == 1:
        draw.line(line, fill='black', width=3, joint='curve')
    with BytesIO() as output:
        im.save(output, format="PNG")
        png = output.getvalue()
    return png

check = [icon(0), icon(1)] # Two states Ready, Unchecked

def mergedicts(dict1, dict2, student):
    if dict2[student] != {} and dict2 != []:
        dict2[student].update(dict1)

    elif dict1 != {}:
        dict2[student] = dict(dict1)
   
def read_json_update_students(students):
    try:
        if(os.path.isfile('Arvostellut.json')):
            f = open('Arvostellut.json', encoding = 'utf-8')
            arvostellut = json.load(f)
            students = arvostellut
            print("STUDENTS LISTA OHJELMAN ALUKSI ON NYT: ", students)
        return students 
    except Exception as e:
        print("File open failed.", e)
        pass


def update_error_points(window, baseinfo, students, treedata):
    alternative_added = False
    try:
        kategoria = ''
        category_sum = clear_sums(window, baseinfo, treedata)
        for student, value in students.items():
            errorpoints = 0
            
            selected_student = students[student]
            remove_excludes(selected_student, baseinfo) # Remove excluded error from list if found
            print(selected_student)
            for error in baseinfo:
                if selected_student != []:
                    if error.error in selected_student.keys():
                        biggest = 0 
                        errorpoints, alternative_added = count_alternative_points(error, baseinfo, selected_student, alternative_added, errorpoints)
                        for i in error.amount:
                            if i == 'All' and selected_student[error.error]==-1:
                                errorpoints = errorpoints + int(error.severity[i])
                                break
                            elif i == 'All' or i == 'virhekoodi':
                                continue
                            
                            if int(i) <= selected_student[error.error]:
                                biggest = i
                            
                        if selected_student[error.error]!=-1 and alternative_added == False and biggest != 0:
                            errorpoints = errorpoints + float(error.severity[str(biggest)])
                            
                        print("Virheen pisteet ovat :",round(errorpoints,1))
                        alternative_added = False
        
            errorpoints = round(errorpoints, 1)
            selected_student['virhepisteet'] = errorpoints
            window['-virheout-'].update(errorpoints)
            print(selected_student)
            
    except UnboundLocalError as e:
        print('Valitse Opiskelija ensin.', e)
        pass
    #Lets clear the variable for new mistake points 
    errorpoints = 0
    

def update_fields(selected_student, students,window, errorlist, k, studentdata, treedata):
    
    node = studentdata.tree_dict[k]
    if node.parent == '':
        pass
    if(selected_student!= node.parent):
        path2 = selected_student.split('/')
        #Checking if main dir if not then take main dir
        
        if path2[-1].endswith('.py'):
            student_path = path2[len(path2)-2]
        # if student _path == 'perus' or student_path == 'tavoite' or student_path == 'minimi':
        #     student_path = path2[len(path2)-1]
        else:
            student_path = path2[len(path2)-1]
            
        
        #Update values since they exist already#
        for student in students:
            if student == student_path:
            #Update mistakepoints on click
                if 'virhepisteet' in students[student_path]:
                    window['-virheout-'].update(students[student_path]['virhepisteet'])
                else:
                    window['-virheout-'].update(0)

                for key in treedata.tree_dict:
                    node =  treedata.tree_dict[key]
                    if key not in students[student] and node.children == []:
                        node =  treedata.tree_dict[key]
                        node.values = 0
                for err in students[student]:
                    if err in treedata.tree_dict:
                        
                        node =  treedata.tree_dict[err]
                        node.values = students[student_path][err]
                        print("NODEN JOTA LÄPIKÄYDÄÄ if ARVOT OVAT:",node.text, node.values)
    window['-TREE-'].update(values = treedata)
            
    if student_path in students:
        if 'virhekoodi' in students[student_path]:
            window['-ERROROUT-'].update(students[student_path]['virhekoodi'][0])
            window['-LEFT-'].update(visible = False)
            window['-RIGHT-'].update(visible = True)

        else:
            window['-RIGHT-'].update(visible=True)
            window['-ERROROUT-'].update('Syötetty koodi näkyy tässä.')
        
    if not students:
        students[student_path] = {}
    if student_path not in students:
        students[student_path] = {}
    window['-TREE-'].update(values = treedata)
    if errorlist:  #check if dict exists
        errorlist.clear()
    return student_path

### Lets make sure that all the category amounts are zero
def clear_sums(ikkuna, list, treedata):
    category_sum = 0
    kategoria = ''
    for error in list:
        node = treedata.tree_dict[error.error]
        parent_node = treedata.tree_dict[node.parent]
        kategoria = parent_node.text
        ikkuna['-TREE-'].update(key = kategoria, value = category_sum)
    return category_sum

def count_alternative_points(error, baseinfo, selected_student, alternative_added, errorpoints):
    if error.alternative:
        for j in error.alternative:
            for alternative in baseinfo:
                if j == alternative.error:
                    amount = str(selected_student[error.error])
                    max_original_points = max(error.severity.values())
                    max_new_points = max(alternative.severity.values())
                    if amount in alternative.severity and alternative_added != True:
                        errorpoints = errorpoints + alternative.severity[amount]
                        print("errorpoints ovat", errorpoints)
                        alternative_added = True    
                    elif max_original_points > max_new_points:
                        errorpoints = errorpoints + max_original_points
                    elif max_new_points > max_original_points:
                        errorpoints = errorpoints + max_new_points
                    #Also fine if mistake points are the same
                    elif selected_student[error.error]==-1:
                        continue
    return errorpoints, alternative_added

def remove_excludes(selected_student, baseinfo):
    for error in baseinfo:
        if error.error in selected_student:
            if selected_student[error.error] == 0:
                del selected_student[error.error]
        if error.exclude:
            print(error.exclude)
            for excluded in error.exclude:
                if error.error in selected_student:
                    if excluded in selected_student:
                        print("Deleting ", excluded)
                        del selected_student[excluded]

def list_to_clipboard(output_list):
    """ Check if len(list) > 0, then copy to clipboard """
    if len(output_list) > 0:
        pyperclip.copy('\n'.join(output_list))
        output_list.clear()
        print('Copied to clipboard: ')
    else:
        print("There was nothing on the clipboard")


            
