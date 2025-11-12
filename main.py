from tkinter import filedialog, messagebox, simpledialog, ttk
import struct, sys, hashlib , binascii, os
import tkinter as tk

data=None
section_data=None
section_number=None
ga_items=[]
event_flag=None
donor_data=None
steam_offset=None
names=[]
MERGED=False

root= tk.Tk()
root.title("Elden Ring Save Fixer")
root.geometry("650x350")
root.resizable(False, False)


working_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_directory)

try:
    with open('donor.data', 'rb') as d:
        donor_data = d.read()
        print('donor len', len(donor_data))
except FileNotFoundError:
    messagebox.showerror("Error", "donor.data file not found. Please ensure it is in the same directory as this script.")
    sys.exit()

def open_file():
    global data

    file_path=filedialog.askopenfilename()
    if file_path:

        with open(file_path, 'rb') as f:
            data=f.read()
    
    names = char_name()
    slot_dropdown["values"] = ["None"] + names
    slot_dropdown.current(0)  # default to None
    print("File loaded, character names updated.")

    messagebox.showinfo("Info", "File loaded successfully. Please select a slot to proceed.")

    return None 


SECTIONS = {
            1: {'start': 0x300, 'end': 0x28030F},
            2: {'start': 0x280310, 'end': 0x50031F},
            3: {'start': 0x500320, 'end': 0x78032F},
            4: {'start': 0x780330, 'end': 0xA0033F},
            5: {'start': 0xA00340, 'end': 0xC8034F},
            6: {'start': 0xC80350, 'end': 0xF0035F},
            7: {'start': 0xF00360, 'end': 0x118036F},
            8: {'start': 0x1180370, 'end': 0x140037F},
            9: {'start': 0x1400380, 'end': 0x168038F},
            10: {'start': 0x1680390, 'end': 0x190039F}
        }


def current_section(number):
    global section_data, section_number

    if data is None:
        messagebox.showerror("Error", "No file loaded!")
        return

    if number not in SECTIONS:
        messagebox.showerror("Error", f"Slot {number} does not exist!")
        return

    section_number = number
    section_info = SECTIONS[number]

    try:
        section_data = data[section_info['start']:section_info['end'] + 1]

        # Check if the slot is empty (4 null bytes at offset 20)
        if section_data[20:24] == b'\x00' * 4:
            messagebox.showerror("Error", f"No character found in slot {number}.")
            return  # stop processing this slot without exiting app

        # continue normal processing
        print(f"Character data found in slot {number}")
        print(f"Section length: {len(section_data)} bytes")


    
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        return


ITEM_TYPE_EMPTY = 0x00000000
ITEM_TYPE_WEAPON = 0x80000000
ITEM_TYPE_ARMOR  = 0x90000000
ITEM_TYPE_AOW  = 0xC0000000    

class Item:

    BASE_SIZE= 8

    def __init__(self, gaitem_handle, item_id, offset , extra=None, size=BASE_SIZE):

        self.gaitem_handle= gaitem_handle
        self.item_id= item_id
        self.extra= extra or {}
        self.size= size
        self.offset= offset

    @classmethod
    def from_bytes(cls, data_type, offset= 0 ):

        gaitem_handle, item_id= struct.unpack_from("<II", data_type, offset)
        type_bits= gaitem_handle & 0xF0000000
        extra = {}
        cursor = offset + cls.BASE_SIZE
        size = cls.BASE_SIZE

        if gaitem_handle != 0:
            if type_bits == ITEM_TYPE_WEAPON:
                extra_4_1 , extra_4_2 , AOW_handle = struct.unpack_from("<II I", data_type, cursor)
                cursor += 12
                extra_1_1 = struct.unpack_from("<B", data_type, cursor)[0]
                cursor += 1
                size = cursor - offset
                
                extra = {
                    "extra_4_1": extra_4_1,
                    "extra_4_2": extra_4_2,
                    "AOW_handle": AOW_handle,
                    "extra_1_1": extra_1_1,
                }
            elif type_bits == ITEM_TYPE_ARMOR:
                extra_4_1 , extra_4_2= struct.unpack_from("<II", data_type, cursor)
                cursor += 8
                size= cursor-offset
                extra= {
                    "extra_4_1": extra_4_1,
                    "extra_4_2": extra_4_2,

                }


        return cls(gaitem_handle, item_id, offset, extra, size)
    


def parse_items(data_type, start_offset, max_slots=5120):
    items = []
    offset = start_offset

    for _ in range(max_slots):
        # Stop if we reach or exceed the end of data
        if offset + Item.BASE_SIZE > len(data_type):
            break

        item = Item.from_bytes(data_type, offset)
        items.append(item)
        offset += item.size  

    return items


def gaprint(data_type):
    global ga_items

    section_data = data_type
    ga_items = []

    start_offset = 0x30

    items = parse_items(section_data, start_offset, max_slots=5120)

    for item in items:
        ga_items.append((item.gaitem_handle, item.item_id, item.offset))


def sort_list():
    global ga_items



    # Then sort by gaitem_handle (1st element)
    ga_items.sort(key=lambda x: x[0])
    print(len(ga_items))

def file_parser():
    global section_data, data, event_flag, steam_offset

    """
    The defined variable is the end of that struct
    """
    gaprint(section_data)
    sort_list()
    section_data=bytearray(section_data)
    ga_item_sorted = sorted(ga_items, key=lambda x: x[2])
    GA_item_handle_size= ga_item_sorted [-1][2] + 8
    Player_data=GA_item_handle_size+ 0x1B0
    SP_effect= Player_data + 0xD0
    equiped_item_index= SP_effect+0x58
    active_equiped_items= equiped_item_index + 0x1c
    equiped_items_id=active_equiped_items+0x58
    active_equiped_items_ga=equiped_items_id+0x58
    iventory_held=active_equiped_items_ga+0x9010
    equiped_spells=iventory_held+0x74
    equiped_items=equiped_spells+ 0x8c
    equiped_gestures= equiped_items+ 0x18
    try:

        equiped_projc_size = struct.unpack_from("<I", section_data, equiped_gestures)[0]
    except struct.error:
        messagebox.showerror("Error", "Found corrupted data too early in the file. Not possible to repair")
        sys.exit()

    equiped_projctile= equiped_gestures + (equiped_projc_size*8 + 4)
    equiped_arraments= equiped_projctile+ 0x9C
    equipe_physics=equiped_arraments+ 0xC
    face_data=equipe_physics+ 0x12f
    inevntory_storage_box= face_data+ 0x6010
    gestures= inevntory_storage_box+ 0x100

    try:
        unlocked_region_size = struct.unpack_from("<I", section_data, gestures)[0]
    except struct.error:
        messagebox.showerror("Error", "Found corrupted data too early in the file. Not possible to repair")
        sys.exit()
    unlocked_region= gestures+ (unlocked_region_size*4 + 4)
    extra_1= 0x1
    horse= unlocked_region+ 0x28+ extra_1
    extra_2= 0x8
    blood_stain=horse+ 0x44 +extra_2
    extra_3= 0x34
    menu_profile= blood_stain+ 0x1008 + extra_3
    ga_items_data_other= menu_profile+ 0x1b588 # need to confirm
    extra_4=0x3
    toturial_data= ga_items_data_other+ 0x408 + extra_4
    total_death=toturial_data+ 0x4
    char_type= total_death+ 0x4
    in_online= char_type+ 0x1
    online_char_type= in_online+0x4
    last_rested_grace=online_char_type+ 0x4
    not_alone_flag= last_rested_grace+ 0x1
    extra_5= 0x4
    ingame_timer= not_alone_flag+ 0x4+ extra_5
    print('help eventfalg star',ingame_timer)
    extra_6= 0x1
    event_flag= ingame_timer+ 0x1bf99f + extra_6
    print('help eventfalg end',event_flag)

    try:
    
        filedarea_size=struct.unpack_from("<I", section_data, event_flag)[0]
        FieldArea= event_flag  + (filedarea_size + 4)

    except struct.error:
        print("Error in Field area size")
        merge_structs()
        return file_parser()

    try:
        worldarea_size = struct.unpack_from("<I", section_data, FieldArea)[0]
    except struct.error:
        print("Error in world area size")
        merge_structs()
        return file_parser()



    WorldArea= FieldArea+ (worldarea_size+4)

    try:

        Worldgeom_size=struct.unpack_from("<I", section_data, WorldArea)[0]
        WorldGeom= WorldArea+ (Worldgeom_size + 4)
    except struct.error:
        print("Error in worldgeom size")
        merge_structs()
        return file_parser()

    try:

        Worldgeom2_size=struct.unpack_from("<I", section_data, WorldGeom)[0]
        WorldGeom2= WorldGeom+ (Worldgeom2_size + 4)
    except struct.error:
        print("Error in worldgeom2 area size")
        merge_structs()
        return file_parser()

    try:
        rendman_size=struct.unpack_from("<I", section_data, WorldGeom2)[0]
        rendman= WorldGeom2+ (rendman_size+4)
    except struct.error:
        print("Error in rendman area size")
        merge_structs()
        return file_parser()

    extra_7=0x2
    player_coord= rendman + 0x3d + extra_7
    extra_8=0x4
    SpawnPointEntityId=player_coord+ 0x4 + extra_8
    extra_9=0x1
    TempSpawnPointEntityId=SpawnPointEntityId +0x4 + extra_9

    NetMan=TempSpawnPointEntityId+0x20004
    WorldAreaWeather=NetMan+0xC
    WorldAreaTime= WorldAreaWeather+0xC
    BaseCharacterVersion=WorldAreaTime+0x10
    print('base char version',BaseCharacterVersion)
    try:
        steam_id_value = struct.unpack_from("<Q", section_data, BaseCharacterVersion)[0]
    except struct.error:
        messagebox.showerror("Error", "Failed to read Steam ID from save file.")
        sys.exit()

    if steam_id_value == 0:
        messagebox.showerror("Error", "Steam ID is zero, invalid save file.")
        
        # Ask user for a valid Steam ID
        steam_id_input = simpledialog.askstring("Input", "Please enter a valid Steam ID:")
        if len(steam_id_input) != 17:
            messagebox.showerror("Error", 'Steam ID should be 17 digits long')

        # Validate input
        if not steam_id_input or not steam_id_input.isdigit():
            messagebox.showerror("Error", "No valid Steam ID provided. Exiting.")
            sys.exit()

        # Convert to integer and write back to section_data
        steam_id_value = int(steam_id_input)
        steam_offset=BaseCharacterVersion
        struct.pack_into("<Q", section_data, BaseCharacterVersion, steam_id_value)
        data=bytearray(data)
        struct.pack_into("<Q", data, 0x19003B4, steam_id_value)
        data=bytes(data)
        messagebox.showinfo("Info", "Steam ID updated successfully. Please Save and Try loading into the game")

    steam_id=BaseCharacterVersion+0x8
    steam_offset=BaseCharacterVersion
    PS5Activity=steam_id+0x20
    DLC_data=PS5Activity+0x32
    PlayerGameDataHash=DLC_data+ 0x80
    section_data=bytes(section_data)
    section_data=section_data
    if MERGED:
        fix_steam_id()

    print('here')#

def fix_steam_id():
    global section_data, data, steam_offset
    steam_id_input = simpledialog.askstring("Input", "Please enter a valid Steam ID:")
    if not steam_id_input or len(steam_id_input) != 17:
        messagebox.showerror("Error", 'Steam ID should be 17 digits long')
        sys.exit()

    # Validate input
    if not steam_id_input.isdigit():
        messagebox.showerror("Error", "No valid Steam ID provided. Exiting.")
        sys.exit()

    # Convert to integer and write back to merged_section
    steam_id_value = int(steam_id_input)
    merged_section = section_data
    merged_section = bytearray(merged_section)
    
    # Check if steam_offset is set
    if steam_offset is None:
        messagebox.showerror("Error", "Steam offset not found. Cannot update Steam ID.")
        sys.exit()
    
    struct.pack_into("<Q", merged_section, steam_offset, steam_id_value)
    merged_section = bytes(merged_section)
    section_data = merged_section

    # Update global data
    data = bytearray(data)
    current_steam = struct.unpack_from("<Q", data, 0x19003B4)[0]
    if current_steam != steam_id_value:
        struct.pack_into("<Q", data, 0x19003B4, steam_id_value)
    data = bytes(data)
    




def merge_structs():
    global event_flag, section_data, donor_data, steam_offset, data, MERGED

    MERGED=True

    event_flag_offset = event_flag

    new_section = section_data[:event_flag]
    # zero out the last 50 bytes in the end of event_flag struct
    new_section[-0x64:] = b'\x00' * 0x64
    

    total_len = len(new_section) + len(donor_data)  # total bytes

    if total_len > 0x280010:
        # Slice donor_data to fit
        donor_data = donor_data[:0x280010 - len(new_section)]
        new_section += donor_data

    elif total_len < 0x280010:
        # Pad with zeros to reach the required length
        padding_length = 0x280010 - total_len
        new_section += donor_data + (b'\x00' * padding_length)

    else:  # total_len == 0x280010
        new_section += donor_data



    data=bytes(data)
    
    section_data = new_section
    messagebox.showinfo("Info", "Save fixed.")




def save_file():
    global section_data, section_number, data

    if section_data is None or section_number is None:
        messagebox.showerror("Error", "No section data to save.")
        return

    section_info = SECTIONS[section_number]
    start = section_info['start']
    end = section_info['end'] + 1

    # Create a mutable bytearray from the original data
    new_data = bytearray(data)

    # Replace the section with the modified section_data
    new_data[start:end] = section_data

    # Ask user for save location
    save_path = filedialog.asksaveasfilename(
    initialfile="ER0000.sl2",  # default file name
    title="Save your file"
)
    if save_path:
        with open(save_path, 'wb') as f:
            f.write(new_data)
        recalc_checksum(save_path)
        messagebox.showinfo("Success", "File saved successfully.")
    recalc_checksum(save_path)
    fix_checksum(save_path)

#Checksum
def recalc_checksum(file):
    """
    Recalculates and updates checksum values in a binary file. Copied from Ariescyn/EldenRing-Save-Manager
    """
    with open(file, "rb") as fh:
        dat = fh.read()
        slot_ls = []
        slot_len = 2621439
        cs_len = 15
        s_ind = 0x00000310
        c_ind = 0x00000300

        # Build nested list containing data and checksum related to each slot
        for i in range(10):
            d = dat[s_ind : s_ind + slot_len + 1]  # Extract data for the slot
            c = dat[c_ind : c_ind + cs_len + 1]  # Extract checksum for the slot
            slot_ls.append([d, c])  # Append the data and checksum to the slot list
            s_ind += 2621456  # Increment the slot data index
            c_ind += 2621456  # Increment the checksum index

        # Do comparisons and recalculate checksums
        for ind, i in enumerate(slot_ls):
            new_cs = hashlib.md5(i[0]).hexdigest()  # Recalculate the checksum for the data
            cur_cs = binascii.hexlify(i[1]).decode("utf-8")  # Convert the current checksum to a string

            if new_cs != cur_cs:  # Compare the recalculated and current checksums
                slot_ls[ind][1] = binascii.unhexlify(new_cs)  # Update the checksum in the slot list

        slot_len = 2621439
        cs_len = 15
        s_ind = 0x00000310
        c_ind = 0x00000300
        # Insert all checksums into data
        for i in slot_ls:
            dat = dat[:s_ind] + i[0] + dat[s_ind + slot_len + 1 :]  # Update the data in the original data
            dat = dat[:c_ind] + i[1] + dat[c_ind + cs_len + 1 :]  # Update the checksum in the original data
            s_ind += 2621456  # Increment the slot data index
            c_ind += 2621456  # Increment the checksum index

        # Manually doing General checksum
        general = dat[0x019003B0 : 0x019603AF + 1]  # Extract the data for the general checksum
        new_cs = hashlib.md5(general).hexdigest()  # Recalculate the general checksum
        cur_cs = binascii.hexlify(dat[0x019003A0 : 0x019003AF + 1]).decode("utf-8")  # Convert the current general checksum to a string

        writeval = binascii.unhexlify(new_cs)  # Convert the recalculated general checksum to bytes
        dat = dat[:0x019003A0] + writeval + dat[0x019003AF + 1 :]  # Update the general checksum in the original data
        print("General Checksum Updated:", new_cs)
        with open(file, "wb") as fh1:
            fh1.write(dat)  # Write the updated data to the file

def char_name():
    global data

    slots = [
        None,
        0x1901D0E,
        0x1901F5A,
        0x19021A6,
        0x19023F2,
        0x190263E,
        0x190288A,
        0x1902AD6,
        0x1902D22,
        0x1902F6E,
        0x19031BA
    ]

    names = []
    max_chars = 16  # 16 UTF-16 characters = 32 bytes

    for i in range(1, 11):
        start = slots[i]
        end = start + max_chars * 2
        raw_name = data[start:end]
        decoded_name = raw_name.decode("utf-16-le", errors="ignore").rstrip("\x00")

        # if empty, show as "Empty Slot i"
        if decoded_name == "":
            decoded_name = f"Empty Slot {i}"

        names.append(decoded_name)

    return names
def fix_checksum(path):
    recalc_checksum(path)
    messagebox.showinfo("Info", "Checksum fixed successfully.")

def on_slot_selected(event):
    val = slot_var.get()
    if val != "None" and not val.startswith("Empty Slot"):
        index = slot_dropdown.current()  # index 1–10 (0 = None)
        print(f"Slot selected: {val} (index {index})")
        current_section(index)  # your function
    else:
        print("No valid slot selected")

# Style configuration
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TLabel", font=("Segoe UI", 10))
style.configure("TCombobox", font=("Segoe UI", 10))
style.configure("Title.TLabel", font=("Segoe UI Semibold", 12))

# Main Frame
main_frame = ttk.Frame(root, padding=15)
main_frame.pack(fill="both", expand=True)

# Title
ttk.Label(main_frame, text="Elden Ring Save File Fix", style="Title.TLabel").pack(pady=(0, 10))

# File controls
file_frame = ttk.Frame(main_frame)
file_frame.pack(fill="x", pady=5)
ttk.Button(file_frame, text="📂 Open File", command=open_file).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(file_frame, text="🛠 Fix My Save", command=file_parser).pack(side="left", expand=True, fill="x", padx=2)
ttk.Button(file_frame, text="💾 Save File", command=save_file).pack(side="left", expand=True, fill="x", padx=2)

# Slot selector
ttk.Label(main_frame, text="Select Slot:").pack(pady=(15, 5))
slot_var = tk.StringVar(value="None")
slot_dropdown = ttk.Combobox(main_frame, textvariable=slot_var, values=["None"], state="readonly", width=35)
slot_dropdown.pack(pady=5)
slot_dropdown.bind("<<ComboboxSelected>>", on_slot_selected)


status = ttk.Label(root, text="Made By Alfazari911", anchor="w", relief="sunken", padding=5)
status.pack(side="bottom", fill="x")

new_label = ttk.Label(root, text="If it did not work, send me ur save at my discord: ALfazari911", anchor="e", padding=5)
new_label.pack(side="top", fill="x")

root.mainloop()