import math

def main():
    #open the existing g-code file
    file = open("g-code.txt", "r")
    content = file.readlines() # gcode as a list where each element is a line
    coordinate_type = 0 if 'G90' in content[0] else 1
    print('Check if coordinate_type is correct! (relative =1, absolute =0) and currently it =', + coordinate_type)
    extruder = 0 if 'T0' in content[6] else 1
    Z_syringe_diameter = float(content[1][20:30])
    A_syringe_diameter = float(content[2][20:30])
    Z_nozzle_diameter = float(content[3][20:30])
    A_nozzle_diameter = float(content[4][20:30])
    extrusion_coefficient = float(content[5][23:30])
    gcode = content[7:]

    # write a new file
    f_new = open("g-code_modified.txt","w+")
    if coordinate_type == 0:
        f_new.write("G90\n")
    else:
        f_new.write("G91\n")
    f_new.write("G21\n") #sets units to millimeters

    x1 = 0
    y1 = 0
    e1 = 0
    a1 = 0
    z1 = 0
    for line in gcode:
        if 'T0' in line:
            f_new.write('T0' + '\n')
            extruder = 0
            # user needs to add pressurize/depressurize e values
        if 'T1' in line:
            f_new.write('T1' + '\n')
            extruder = 1
            # user needs to add pressurize/depressurize e values
        else:
            letters = {'G': None, 'X': None, 'Y': None, 'Z': None, 'A': None, 'I': None, 'J': None, 'R': None, 'T': None, 'E': None, 'F': None}
            for command in line.split():
                letters[command[0]] = float(command[1:])
            keys = sorted(letters.keys())
            a, e, f, g, i, j, r, t, x, y, z = [letters[key] for key in keys]
            #calculate extrusion distance
            l = 0
            e = None
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
            if e is not None:
                write_line += ' E' + str(e)
            if f is not None:
                write_line += ' F' + str(f)
            f_new.write(write_line + "\n")

            x1 = x_val if x_val is not None else x1
            y1 = y_val if y_val is not None else y1
            z1 = z_val if z_val is not None else z1
            a1 = a_val if a_val is not None else a1
            e1 = e if e is not None else e1
    f_new.close()
    file.close()

if __name__== "__main__":
    main()

