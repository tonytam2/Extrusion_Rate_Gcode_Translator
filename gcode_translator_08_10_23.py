import math
import re

def headerFindDigit(line):
    matchArray = re.search('\d+\.?\d*', line)
    if(matchArray is None): #returns the keyword None if no digits are found
        print('No digits were found in: ' + line)
        return matchArray;
    print(line)
    return matchArray

def main():
    #open the existing g-code file
    file = open("gcode.txt", "r")
    content = file.readlines() # gcode as a list where each element is a line
    coordinate_type = 0 if 'G90' in content[0] else 1
    if coordinate_type == 0: print('You are currently in G90 ABSOLUTE mode.')
    if coordinate_type == 1: print('You are currently in G91 RELATIVE mode.')

    Z_syringe_line             = headerFindDigit(content[1]) 
    A_syringe_line             = headerFindDigit(content[2])
    Z_nozzle_line              = headerFindDigit(content[3])
    A_nozzle_line              = headerFindDigit(content[4])
    extrusion_coefficient_line = headerFindDigit(content[5])

    Z_syringe_diameter    = float(Z_syringe_line.group(0)) if Z_syringe_line is not None else 0
    A_syringe_diameter    = float(A_syringe_line.group(0)) if A_syringe_line is not None else 0
    Z_nozzle_diameter     = float(Z_nozzle_line.group(0)) if Z_nozzle_line is not None else 0
    A_nozzle_diameter     = float(A_nozzle_line.group(0)) if A_nozzle_line is not None else 0
    extrusion_coefficient = float(extrusion_coefficient_line.group(0)) if extrusion_coefficient_line is not None else 0

    gcode = content[6:]
    extruder = 0
    b_extrusion = False
    c_extrusion = False
    # write a new file
    f_new = open("gcode_modified.txt","w+t")
    if coordinate_type == 0:
        f_new.write("G90\n")
    else:
        f_new.write("G91\n")
    #f_new.write("G21\n") #sets units to millimeters

    x1 = 0 #initialize values for G90 relative coordinate difference calculations
    y1 = 0
    e1 = 0
    a1 = 0
    z1 = 0
    for line in gcode:
        # JW 9/21/22 allow G92 E0 to reset relative E calculations in G90. 
        # Allows running script with multiple separated paths in G90, but user MUST write G92 E0 in between distinct paths.
        if 'G92 E0' in line:
            # reset relative coordinates to 0 for calculations below.
            x1 = 0 
            y1 = 0
            e1 = 0
            a1 = 0
            z1 = 0
        # JW 1/21/22 Skip/copy lines that are empty or comments. Allows skipping lines if "NO E" is in comments      
        if line[0] == ';' or line == '\n' or 'G90' in line or 'G91' in line or 'G92' in line or 'G21' in line or 'M2' in line or 'G4' in line:
            f_new.write(line)
            continue
        if 'T0' in line:
            f_new.write('T0' + '\n')
            extruder = 0
            continue
            # user needs to add pressurize/depressurize e values
        if 'T1' in line:
            f_new.write('T1' + '\n')
            extruder = 1
            continue
            # user needs to add pressurize/depressurize e values
        if line[0] == 'K' or line[0] == 'k':
            new_k = (line.split(' = '))
            extrusion_coefficient = float(new_k[-1])
            # print(extrusion_coefficient)
            f_new.write("; extrusion coefficisent changed to = " + str(extrusion_coefficient) + '\n')
            continue
            # reset the extrusion coefficient
        if line[0] == 'B' or line[0] == 'b':
            b_extrusion = True
            c_extrusion = False
            continue
        if line[0] == 'C' or line[0] == 'c':
            c_extrusion = True
            b_extrusion = False
            continue
        
        else:
            letters = {'G': None, 'X': None, 'Y': None, 'Z': None, 'A': None, 'I': None, 'J': None, 'R': None, 'T': None, 'E': None, 'F': None}
            var = False #see trigger below
            for command in line.split(): #iterates through each element in a line
                if command[0] == ';' : #Fixes bug where script tries to read inline comments. This will delete the comment :( JW 1/27/22
                    break
                if command[-1] == ';':
                    command = command[0:-1] #Remove ; if it's at the end of an element
                    var = True #Fixes bug where script tries to read inline comments. This will delete the comment :( JW 1/27/22
                letters[command[0]] = float(command[1:])
                if var == True: #Fixes bug where script tries to read inline comments. This will delete the comment :( JW 1/27/22
                    break

            if not any((letters[c] for c in 'XYZAIJRT')): #If line contains only G, E, and F, it is probably a pressurization line, so ignore. JW 1/27/22
                f_new.write(line)
                continue
            keys = sorted(letters.keys())
            a, e, f, g, i, j, r, t, x, y, z = [letters[key] for key in keys]
            #calculate extrusion distance
            l = 0 #length of line
            e = None #extrusion value
            vals = [a, i, j, x, y, z]
            a_val, i_val, j_val, x_val, y_val, z_val = [val if val is not None else 0 for val in vals]
            rel_vals = [(a, a1), (x, x1), (y, y1), (z, z1)]
            a_rel, x_rel, y_rel, z_rel = [val[0] - val[1] if val[0] is not None else 0 for val in rel_vals]
            if g == 1:
                    # volume extruded is E distance * pi * (barrel diameter/2)^2 volume that comes out is k*length * pi * (nozzle_diameter/2)^2
                    # E = (l*pi*(nozzle_diameter/2)^2)/(pi * (barrel diameter/2)^2)
                    # E = (k*l*nozzle_diameter^2)/(barrel diameter^2)
                #relative
                if coordinate_type == 1: #relative
                    l = math.sqrt(x_val ** 2 + y_val ** 2 + a_val ** 2 + z_val ** 2)
                elif coordinate_type == 0:  # absolute
                    l = math.sqrt(x_rel ** 2 + y_rel ** 2 + a_rel ** 2 + z_rel ** 2)
            elif g==2 or g==3: #g2 and g3
                full_circle = False
                radius = r
                if radius is None:
                    radius = math.sqrt((i_val ** 2) + (j_val ** 2))
                if coordinate_type == 1: #relative
                    if x_val or y_val or z_val or a_val != 0:
                        d = math.sqrt(x_val ** 2 + y_val ** 2 + a_val ** 2 + z_val ** 2)
                        theta = 2*math.pi - math.acos((1 - (d ** 2 / (2 * radius ** 2))))
                    else:
                        theta = 2 * math.pi #full circle
                        full_circle = True
                elif coordinate_type == 0: #absolute
                    if x_val or y_val or z_val or a_val is not None:
                        d = math.sqrt(x_rel ** 2 + y_rel ** 2 + a_rel ** 2 + z_rel ** 2)
                        theta = 2*math.pi - math.acos((1- (d ** 2 / (2 * radius ** 2))))
                    else:
                        theta = 2 * math.pi
                        full_circle = True
                l = radius * theta #arclength
                if g==3 and full_circle == False:
                    l = 2 * math.pi * radius - l #counter-clockwise
            if coordinate_type == 1: #relative
                if extruder == 0:
                    e = (extrusion_coefficient * l * Z_nozzle_diameter ** 2) / (Z_syringe_diameter ** 2)
                if extruder == 1:
                    e = (extrusion_coefficient * l * A_nozzle_diameter ** 2) / (A_syringe_diameter ** 2)

            elif coordinate_type == 0: #absolute
                if extruder ==0:
                    e = e1+(extrusion_coefficient * l * Z_nozzle_diameter ** 2) / (Z_syringe_diameter ** 2)

                if extruder ==1:
                    e = e1+(extrusion_coefficient * l * A_nozzle_diameter ** 2) / (A_syringe_diameter ** 2)

            write_line = ""
            if g is not None:
                write_line += 'G' + str(int(g))
            if x is not None:
                write_line += ' X' + str(x)
            if y is not None:
                write_line += ' Y' + str(y)
            if g == 2 or g == 3:
                if r is not None:
                    write_line += ' R' + str(r)
                if i is not None:
                    write_line += ' I' + str(i)
                if j is not None:
                    write_line += ' J' + str(j)
            if z is not None:
                write_line += ' Z' + str(z)
            if a is not None:
                write_line += ' A' + str(a)
            if e is not None and g != 0:
                if b_extrusion == True:
                    write_line += ' B' + str(round(e,3))
                elif c_extrusion == True:
                    write_line += ' C' + str(round(e,3))
                else:
                    write_line += ' E' + str(round(e,3))
            if f is not None:
                write_line += ' F' + str(f)

            #override write_line to be original line if NO E is written. This also allows the script to remember current location even when there is no extrusion (relevant for G90 codes)
            if 'NO E' in line:
                f_new.write(line)
                e -= (extrusion_coefficient * l * Z_nozzle_diameter ** 2) / (Z_syringe_diameter ** 2) #undo the E value increment for lines that don't have extrusion (relevant for G90)
            else:
                #Write line    
                f_new.write(write_line + "\n")

            x1 = x_val if x_val is not None else x1
            y1 = y_val if y_val is not None else y1
            z1 = z_val if z_val is not None else z1
            a1 = a_val if a_val is not None else a1
            e1 = e if e is not None else e1
    f_new.close()
    file.close()

import subprocess, os, platform

#Open file automatically after running the script
filepath = "gcode_modified.txt"

if platform.system() == 'Darwin':       # macOS
    subprocess.call(('open', filepath))
elif platform.system() == 'Windows':    # Windows
    try:
        os.startfile(filepath)
    except FileNotFoundError:
        print(filepath + " was not found.")
else:                                   # linux variants
    subprocess.call(('xdg-open', filepath))

if __name__== "__main__":
    main()

