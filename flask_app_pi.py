from __future__ import print_function
import datetime, time, sqlite3, os
import P17_003, P17_011R2, P17_031A
from flask import Blueprint, render_template, request, redirect, url_for, make_response
from flask import session, send_from_directory
import command_parse

pi_blueprint = Blueprint('pi_blueprint', __name__)

def get_printable_dict(dct):
    ret = ""
    if dct is None:
        return ret
    
    now = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    ret+=(now+'\n')
    SFP_pages = ['A0L', 'A0U', 'A2L', 'A2U', 'A2U00', 'A2U01', 'A2U02']
    for key in SFP_pages:
        if(key in dct.keys()):
            dct[key] = dct[key].upper()
            ret += "{} {}\n\n".format(key, dct[key])

    return ret

def get_list_string(lst):
    ret = ""
    if lst is None:
        return ret

    now = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    ret+=(now+'\n')
    for item in lst:
        item[0]=item[0].rstrip()
        item[1] = item[1].upper()
        ret += "{} {}\n".format(item[0], item[1])
    return ret
def run_P17_011R2(file = None, string = None, main_page = True):
    """Daniel's code
    def is_valid(string):
        return string[:2] not in ['00', 'FF', 'ff']

    if is_valid(string):"""
    P17_011R2.fLog_Path = file
    P17_011R2.bPrint = False
    P17_011R2.display_parameters(string, main_page)

#==========================================PI UI===============================#

@pi_blueprint.route('/pro_coder')
def pro_coder(item = None):

    hex_templates = (request.args.get("hex_templates") if(request.args.get("hex_templates")) else "")
    read_codes = (request.args.get("read_codes") if(request.args.get("read_codes")) else "")
    new_codes_hex = (request.args.get("new_codes_hex") if(request.args.get("new_codes_hex")) else "")
    return_dict = (request.args.get("return_dict") if(request.args.get("return_dict")) else "")

    write_response = request.args.get("write_response") if (request.args.get("write_response")) else 0
    debug_mode = request.args.get("debug_mode") if (request.args.get("debug_mode")) else 0

    with open('tmp1.out', 'r') as f:
        parse_str1 = f.read()

    with open('tmp2.out', 'r') as f:
        parse_str2 = f.read()

    with open('tmp3.out', 'r') as f:
        parse_str3 = f.read()

    with open('tmp4.out', 'r') as f:
        parse_str4 = f.read()

    return render_template('pro_coder.html', name = "pro_coder",
        station_id = request.cookies.get('station_id'), PI2 = request.cookies.get('PI2'),
        formfactor = request.cookies.get('formfactor'), part_code = request.cookies.get('partcode'),
        parse_return1 = parse_str1, parse_return2 = parse_str2, parse_return3 = parse_str3,
        parse_return4 = parse_str4, item = request.args.get('item'), write_response = write_response,
        debug_mode = debug_mode, hex_templates = hex_templates, read_codes = read_codes,
        new_codes_hex = new_codes_hex, return_dict = return_dict)

@pi_blueprint.route('/setup', methods = ['POST'])
def setup():

    station_id, operator = request.form.get('station_id'), request.form.get('operator')
    transceiver_password= request.form.get('password')
    part_code, po_number = request.form.get('part_code'), request.form.get('po_number')
    qa_mode = request.form.get('qa_mode')

    form_factor = 'SFP'

    read_codes, templates, hex_templates, new_codes_hex, return_dict = {}, {}, {}, {}, {}
    default_page = ""
    write_response = ""

    if(not part_code):
        read_codes, default_page = read_code(form_factor, transceiver_password)
    else:
        #grab tuple of dictionary hex, change to dynamic later
        templates, hex_templates = P17_031A.getTemplates(part_code, form_factor)
        #flask_app.insert_into_pioutput(form_factor, 0, hex_templates, pilogID)
        #dictionary with all the pages available
        read_codes, default_page = read_code(form_factor, transceiver_password)
        #flask_app.insert_into_pioutput(form_factor, 1, read_codes, pilogID)
        new_codes_hex = P17_031A.getNewCode(templates, read_codes, form_factor)
        #flask_app.insert_into_pioutput(form_factor, 2, new_codes_hex, pilogID)
        write_response, return_dict = write_to_pi(new_codes_hex, default_page, form_factor)
    if(hex_templates and hex_templates['A0L']):
        run_P17_011R2('/home/pi/web_app/tmp1.out', hex_templates['A0L'])
    else:
        with open('/home/pi/web_app/tmp1.out', 'w') as f:
            f.truncate()
    if(read_codes and read_codes['A0L']):
        run_P17_011R2('/home/pi/web_app/tmp2.out', read_codes['A0L'])
    else:
        with open('/home/pi/web_app/tmp2.out', 'w') as f:
            f.truncate()
    if(new_codes_hex and new_codes_hex['A0L']):
        run_P17_011R2('/home/pi/web_app/tmp3.out', new_codes_hex['A0L'])
    else:
        with open('/home/pi/web_app/tmp3.out', 'w') as f:
            f.truncate()
    if(return_dict and return_dict.has_key('A0L')):
        run_P17_011R2('/home/pi/web_app/tmp4.out', return_dict['A0L'])
    else:
        with open('/home/pi/web_app/tmp4.out', 'w') as f:
            f.truncate()


    resp = redirect(url_for('pi_blueprint.pro_coder', item = "4", write_response = write_response,
        hex_templates = get_printable_dict(hex_templates),
        read_codes = get_printable_dict(read_codes),
        new_codes_hex = get_printable_dict(new_codes_hex),
        return_dict = get_printable_dict(return_dict)))
    return resp
    
@pi_blueprint.route('/read_code', methods = ['POST', 'GET'])
def read_code(form_factor = None, transceiver_password = None):
    codes = {}
    formfactor = form_factor
    codes, default_page = read_transceiver(formfactor, transceiver_password)

    return codes, default_page

def read_transceiver(formfactor, transceiver_pwd):
    codes = {}
    if(formfactor == 'SFP'):
        SFP_pages = ['A0L', 'A0U', 'A2U', 'A2L', 'A2U00', 'A2U01', 'A2U02']
        
        default_page = command_parse.exec_cmd('A2,0x7F??1')
        if ('True' not in command_parse.exec_cmd('A2,0x7F=00?!')):
            SFP_pages.remove('A2U00')
        if ('True' not in command_parse.exec_cmd('A2,0x7F=01?!')):
            SFP_pages.remove('A2U01')
        if ('True' not in command_parse.exec_cmd('A2,0x7F=02?!')):
            SFP_pages.remove('A2U02')
        for page in SFP_pages:
            codes[page] = read_page(page, default_page)
    elif(formfactor=='QSFP' or formfactor =='XFP'):
        XFP_pages = ['A0L', 'T00', 'T01', 'T02']
        
        default_page = command_parse.exec_cmd('A0,0x7F??1')
        if ('True' not in command_parse.exec_cmd('A0,0x7F=00?!')):
            SFP_pages.remove('T00')
        if ('True' not in command_parse.exec_cmd('A0,0x7F=01?!')):
            SFP_pages.remove('T01')
        if ('True' not in command_parse.exec_cmd('A0,0x7F=02?!')):
            SFP_pages.remove('T02')
        
        for page in XFP_pages:
            codes[page] = read_page(page, default_page)
            
    return codes, default_page

def read_page(page, default_page):
    #commands = {'A0L' : 'A0,0x00??128', 'A0U' : 'A0,0x80??128'
    #, 'A2L', 'A2U00', 'A2U01', 'A2U02', 'T00', 'T01', 'T02'}

    if page == 'A0L':
        return command_parse.exec_cmd('A0,0x00??128')
        #return client.send_cmd(ssh, 'A0,0x00??128')
    elif page =='A0U':
        return command_parse.exec_cmd('A0,0x80??128')
        #return client.send_cmd(ssh, 'A0,0x80??128')
    elif page == 'A2L':
        return command_parse.exec_cmd('A2,0x00??128')
        #return client.send_cmd(ssh, 'A2,0x00??128')
    elif page == 'A2U00':
        command_parse.exec_cmd('A2,0x7F=00')
        return command_parse.exec_cmd('A2,0x80??128')
    elif page == 'A2U01':
        command_parse.exec_cmd('A2,0x7F=01')
        return command_parse.exec_cmd('A2,0x80??128')
    elif page == 'A2U02':
        command_parse.exec_cmd('A2,0x7F=02')
        return command_parse.exec_cmd('A2,0x80??128')
    elif page == 'A2U':
        command_parse.exec_cmd('A2,0x7F='+default_page)
        return command_parse.exec_cmd('A2,0x80??128')
    elif page == 'T00':
        command_parse.exec_cmd('A0,0x7F=00')
        return command_parse.exec_cmd('A0,0x80??128')
    elif page == 'T01':
        command_parse.exec_cmd('A0,0x7F=01')
        return command_parse.exec_cmd('A0,0x80??128')
    elif page == 'T02':
        command_parse.exec_cmd('A0,0x7F=02')
        return command_parse.exec_cmd('A0,0x80??128')
    else:
        return "Unfound page error"

@pi_blueprint.route('/write_to_pi', methods = ['POST'])
def write_to_pi(new_codes_hex = None, default_page = None, form_factor = None):

    command_parse.exec_cmd('A2,0x7F='+default_page)
    write_response = True
    return_dict = {}
    for new_code in new_codes_hex.keys():
        if(new_code == "A0L"):
            output = command_parse.exec_cmd("A0,0x00=#"+new_codes_hex["A0L"].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A0U"):
            output = command_parse.exec_cmd("A0,0x80=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A2L"):
            output = command_parse.exec_cmd("A2,0x00=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A2U"):
            output = command_parse.exec_cmd("A2,0x80=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A2U00" and "00" not in default_page):
            command_parse.exec_cmd('A2,0x7F=00')
            output = command_parse.exec_cmd("A2,0x80=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A2U01" and "01" not in default_page):
            command_parse.exec_cmd('A2,0x7F=01')
            output = command_parse.exec_cmd("A2,0x80=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")
        elif(new_code == "A2U02" and "02" not in default_page):
            command_parse.exec_cmd('A2,0x7F=02')
            output = command_parse.exec_cmd("A2,0x80=#"+new_codes_hex[new_code].upper())
            if('False' in output):
                write_response = False 
            return_dict[new_code] = output.replace('False', "").replace('True', "")

        return write_response, return_dict
        
@pi_blueprint.route('/pro_reader')
def pro_reader(outputlist = [], cmdlist = []):
    
    upload_user = (request.args.get("upload_user") if(request.args.get("upload_user")) else "0")
    command = (request.args.get("command") if(request.args.get("command")) else None)
    output_content = (request.cookies.get('Output Content') if(request.cookies.get('Output Content')) else "")
    options = (request.cookies.get('Options') if(request.cookies.get('Options')) else "")
    with open('/home/pi/web_app/tmp1.out', 'r') as f:
        parse_return1 = f.read()
    return render_template('ProReader.html', name = "proreader",
                            parse_return1 = parse_return1,
                            command = command,
                            options = options,
                            upload_user = upload_user,
                            output_content = output_content)


@pi_blueprint.route('/check_connection', methods = ['POST'])
def check_connection():
    
    email = request.form.get('email')
    output_content = ""
    string = ""
    filename = "database.db"
    upload_user = 0
    if(email == 'eng@prolabs.com'):
        upload_user = 1
    else:
        output_content = (request.cookies.get("output_content") if(request.cookies.get("output_content")) else "")
        try:
            byte=command_parse.exec_cmd('A0,0x00??')
            output_content+="Connection Open...\n"
            sDatabase_File = '/home/pi/web_app/useruploads/{}'.format(filename)
            conn = sqlite3.connect(sDatabase_File)
            c = conn.cursor()
            c.execute('SELECT firstbyte from Configuration')
            c.execute("SELECT options from Configuration WHERE firstbyte = '{}'".format(byte))
            lst=c.fetchall()
            string = ""
            for i in lst:
                string+=i[0]+"\n"
        except Exception, e:
            output_content+="Connection Failed...\n"
        
    resp = make_response(redirect(url_for('pi_blueprint.pro_reader', upload_user = upload_user, 
                                output_content = output_content,
                                options = string)))
    resp.set_cookie("Options", string)
    resp.set_cookie("Output Content", output_content)
    resp.set_cookie("Email", email)
    return resp
    
@pi_blueprint.route('/pi_bulk_input', methods = ['POST'])
def pi_bulk_input():
    command = request.form.get('command_select')
    commands = request.form.get('commands')
    return_lst = []
    output_content = (request.cookies.get("output_content") if(request.cookies.get("output_content")) else "")
    if(len(commands)>0):
        if('\r' in commands):
            cmds = commands.split('\r')
        else:
            cmds=commands.split('\n')
        for cmd in cmds:
            output = command_parse.exec_cmd(cmd)
            return_lst.append([cmd, output])
        
        output_content+=get_list_string(return_lst)
            
    else:
        if(command == 'SFP/SFP+/SFP28'):
            read_codes, default_page = read_code('SFP')
            SFP_pages = ['A0L', 'A0U', 'A2L', 'A2U', 'A2U00', 'A2U01', 'A2U02']
            for key in SFP_pages:
                if(key in read_codes.keys()):
                    if(key == 'A0L'):
                        main_page = True
                    else:
                        main_page = False
                    with open('/home/pi/web_app/tmp1.out', 'a') as f:
                        f.write('\n'+ key + '\n')
                    run_P17_011R2('/home/pi/web_app/tmp1.out', read_codes[key], main_page)
            command_parse.exec_cmd('A2,0x7F='+default_page)
            output_content+=get_printable_dict(read_codes)
        elif ('QSFP' in command or 'XFP' in command):
            #QSFP and XFP have the same read pattern
            read_codes = read_code('XFP')
            XFP_pages = ['A0L', 'T00', 'T01', 'T02']
            for key in XFP_pages:
                if(key in read_codes.keys()):
                    if(command == 'QSFP' and key == 'T00'):
                        main_page = True
                    elif(command=='XFP' and key =='T01'):
                        main_page=True
                    else:
                        main_page = False
                    with open('/home/pi/web_app/tmp1.out', 'a') as f:
                        f.write('\n'+ key + '\n')
                    run_P17_011R2('/home/pi/web_app/tmp1.out', read_codes[key], main_page)
            command_parse.exec_cmd('A2,0x7F='+default_page)
            output_content+=get_printable_dict(read_codes)
        elif('T00' in command or 'T01' in command or 'T02' in command):
            default_page = command_parse.exec_cmd('A0,0x7F??')
            if('T00' in command):
                command_parse.exec_cmd('A0,0x7F=00')
                output = command_parse.exec_cmd('A0,0x80??128')
                return_lst.append(['T00',])
                with open('/home/pi/web_app/tmp1.out', 'a') as f:
                        f.write('\n'+ 'T00' + '\n')
                run_P17_011R2('/home/pi/web_app/tmp1.out', output, True)
            elif('T01' in command):
                command_parse.exec_cmd('A0,0x7F=01')
                return_lst.append(['T01',command_parse.exec_cmd('A0,0x80??128')])
            elif('T02' in command):
                command_parse.exec_cmd('A0,0x7F=02')
                return_lst.append(['T02',command_parse.exec_cmd('A0,0x80??128')])
            output_content+=get_list_string(return_lst)            
            command_parse.exec_cmd('A0,0x7F='+default_page)
        else:
            cmd = get_cmd(command)
            output = command_parse.exec_cmd(cmd)
            return_lst.append([cmd, output])
            with open('/home/pi/web_app/tmp1.out', 'a') as f:
                f.write('\n'+ command + '\n')
            if('=' not in cmd and '?' in cmd):\
                run_P17_011R2('/home/pi/web_app/tmp1.out', output, command=='A0L')
            output_content+=get_list_string(return_lst)
    resp = redirect(url_for('pi_blueprint.pro_reader', 
                            output_content = output_content))
    resp.set_cookie("Output Content", output_content)
    return resp
    
def get_cmd(x):
    return {
        'A0L': "A0,0x00??128",
        'A0U': "A0,0x80??128",
        'A2L': "A2,0x00??128",
        'A2U': "A2,0x80??128"
    }.get(x, "")
    
@pi_blueprint.route('/clear_output', methods = ['POST', 'GET'])
def clear_output():
    output_content = ""
    with open('/home/pi/web_app/tmp1.out', 'w') as f:
            f.truncate()
    resp = redirect(url_for('pi_blueprint.pro_reader', output_content = output_content))
    resp.set_cookie("Output Content", "")
    return resp
"""
@pi_blueprint.route('/download_log',methods=['GET'])
def download_log():
    filename = "userLog.txt"
    with open(filename, 'w') as f:
        f.truncate()
    with open('tmp1.out') as f:
        lines = f.readlines()
        output_content = (request.cookies.get('Output Content') if(request.cookies.get('Output Content')) else "")
        with open(filename, 'w') as f:
            f.write(output_content)
            f.writelines(lines)
    #return flask_app.app.send_static_file('userLog.txt')

    return send_from_directory(directory=flask_app.app.root_path, filename=filename, as_attachment=True)"""

@pi_blueprint.route('/submit_file', methods = ['POST'])
def submit_file():
    file = request.files['file']
    filename = "/home/pi/web_app/useruploads/{}".format("database.db")
    first_byte = request.cookies.get("First Byte")
    file.save(filename)
    return redirect(url_for('pi_blueprint.pro_reader'))
