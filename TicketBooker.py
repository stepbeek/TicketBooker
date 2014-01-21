#! /usr/bin/env

# TicketBooker - Books tickets for a venue. 
# Author: Stephen van Beek
# ---------------------------

import itertools
import threading
import time
import pickle
import getpass


class Venue:
    def __init__(self, num_seats_per_row=1, num_rows=1, rows = [], booker = {}):
        self.lock = threading.RLock()
        self.num_seats = num_seats_per_row
        self.num_rows = num_rows
        if len(rows) >0:
            self.rows = rows
        else:
            self.rows = [[0 for i in range(num_seats_per_row)] for j in range(num_rows)]
        self.booker = booker
        self.best = []

    def CreateUser(self,name,password):
        if self.booker.keys().count(name) == 0:
            self.booker[name] = [[],[]]
            self.booker[name][0].append(password)
            return True
        else:
            print "It appears that username is already taken. \nPlease try again."
        return False
            
    def LoginUser(self,name,password):
        if self.booker.keys().count(name) == 1:
            if self.booker[name][0].count(password) == 1:
                print "Thank you."
                return True
            else:
                print "The password you entered was incorrect"
                return False
        else:
            print "That user does not exist."
            return False

    #Checks number of available seats
    def CountAvail(self):
        with self.lock:
            number = 0
            for i in self.rows:
                number += i.count(0)
        return number
    
    # Checks that seat actually exists
    def CheckValid(self, row, seat):
        if row < 0 or row > (self.num_rows -1):
            return False
        if seat < 0 or seat > (self.num_seats -1):
            return False
        return True

    # Allows a user to book a select block of seats on a single row
    def BookSelectBlock(self, row, start, coun, name):
        with self.lock:
            #Check each seat is valid.
            for i in range(coun):
                if not self.CheckValid(row-1,start -1 +i):
                    print("That selection is invalid, plase try again.")
                    return False

            # Check each seat is available.
            for i in range(coun):
                if not self.CheckAvail(row-1,start-1 + i):
                    print "Seat no. "+ str(row-1) + "," + str(start-1) +" is already taken."
                    return False

        self.BookBlock(row-1,start-1,coun, name)
        return True

    #Checks that seat is available
    def CheckAvail(self, row, seat):
        if self.rows[row][seat] != 0:
            return False
        return True
    
    # Indiscriminantly books a block of seats
    def BookBlock(self, row, start, coun, name):
        for i in range(coun):
            self.rows[row][start + i] = 1
            self.booker[name][1].append((row+1, start+1+i))
        print "Seats booked successfully"
        print "Block booked from seat " + str(start+1) + " to " + str(start+coun) + " on row " + str(row+1) + "."
        return True
    
    # Finds number and location of adjacent seats in best row
    def BookAdj(self, coun, name):
        # Create a list to find best compromise
        self.best = []
        # Search each row for perfect block, noting each free block along the way.
        for i in range(self.num_rows):
            availBlock = 0
            row_count = 0
            for j in range(self.num_seats):
                if self.CheckAvail(i,j):
                    # if seat is actually available
                    availBlock += 1
                    # When first suitable block is found, book it and exit.
                    if availBlock >= coun:
                        start = j +1 - coun
                        self.BookBlock(i,start, coun, name)
                        #print "Block booked on row " + str(i+1) + ", from seat " + str(start+1) + " to seat " + str(start+coun) + "."
                        return True
                    if (j == self.num_seats -1) and availBlock>1:
                        self.best.append([i,j+1-availBlock,availBlock])
                        if availBlock == self.num_seats:
                            row_count+=1
                            if self.num_seats*row_count>=coun:
                                return False
                elif availBlock > 1 and not self.CheckAvail(i,j):
                    # If seat not available
                    self.best.append([i,j - availBlock, availBlock])
                    availBlock = 0
        return False

    #Finds the distances involved in combinations of seats
    def DistFinder(self, combs,i):
        min_row = min(sumofcombo[0] for sumofcombo in combs[i])
        max_row = max(sumofcombo[0] for sumofcombo in combs[i])
        row_diff = abs(max_row - min_row)
        min_seat_centre = min((combo[1] + (combo[2])/2 - 1)  for combo in combs[i])
        max_seat_centre = max((combo[1] + (combo[2])/2 - 1)  for combo in combs[i])
        seat_diff = abs(max_seat_centre - min_seat_centre)
        return [i, row_diff, seat_diff]

    # Counts the number of chunks a group is split into for a split booking
    def MinSplit(self, comb, dist):
        splitCount = []
        minNoOfSplit = len(comb[1])
        for i in range(len(comb)):
            if len(comb[i])<minNoOfSplit:
                splitCount = []
                splitCount.append([i,len(comb[i])])
                minNoOfSplit = len(comb[i])
            elif len(comb[i]) == minNoOfSplit:
                splitCount.append([i,len(comb[i])])
        minSplitCombs = [dist[i[0]] for i in splitCount]
        return minSplitCombs


    # Returns only those combinations with the minimum separation of rows
    def MinRowDist(self, minSplitCombs):
        # Set the minimum to be the first value in the list
        minSplits = minSplitCombs[0][1]
        minRowCombs = []
        for i in minSplitCombs:
            if i[1] < minSplits:
                minRowCombs = [i]
                minSplits = i[1]
            elif i[1] == minSplits:
                minRowCombs.append(i)
        return minRowCombs


    # Find all possible combinations of chunks of seats that add to exactly the number of seats sought
    def AllCombs(self, avail, coun):
        combs = []
        n = len(avail)
        i = int(coun/self.num_seats)
        while i<=n:
            els = [list(x) for x in itertools.combinations(avail,i)]
            for j in els:
                if sum(sumofcombo[2] for sumofcombo in j) == coun:
                    n = i
                    combs.append(j)
                elif sum(sumofcombo[2] for sumofcombo in j) > coun:
                    n = i
                    b = coun
                    j[-1] = [j[-1][0], j[-1][1], j[-1][2] + (b - sum(x[2] for x in j))]
                    combs.append(j)
            i += 1
        return combs


    # If user just wants a selection of seats
    def AnyBlockBook(self, coun, name):
        with self.lock:
            if self.BookAdj(coun, name):
                return True
            else:
                while True:
                    ans = raw_input("Would you like to split the block into chunks? y or n?")
                    if ans.upper() == "Y" or ans.upper() == "YES":
                        if sum(seatsAvail[2] for seatsAvail in self.best)<coun:
                            print "There are not enough free seats left"
                            return False
                        else:
                            combs = self.AllCombs(self.best, coun)
                        dist = []
                        for i in range(len(combs)):
                            dist.append(self.DistFinder(combs,i))
                        # Now we have list dist which is composed of nothing but combinations of seats adding 
                        # to coun in form, [combo number, row distance, seat distance].
                        minSplitCombs = self.MinSplit(combs,dist)
                        # Now we have minSplitCombs, a list of the combinations in the same format as above 
                        # with the least possible splits
                        # We now find the least distance in rows, with seat centre as a secondary consideration
                        minRowCombs = self.MinRowDist(minSplitCombs)

    
                        if len(minRowCombs) == 1: # That is if only one combination had a minimal distance between rows.
                            unordered_choice = combs[(minRowCombs[0][0])]
                            ordered_choice = self.SortPrefer(unordered_choice)
                        elif len(minRowCombs) > 1: # That is if multiple seats had the same distance in rows, we check for the greatest distance in seats.
                            p = self.MinSeatDist(minRowCombs)
                            # Now we have p which is composed of the combinations with equal minimum distance, so we just pick the one with the lowest row combination
                            unordered_choice = self.ChooseBestCombo(combs,p)
                            ordered_choice = self.SortPrefer(unordered_choice)

                        for i in ordered_choice:
                            if coun - i[2] >1:
                                self.BookBlock(i[0], i[1],i[2], name)
                                coun -= i[2]
                            elif coun - i[2] == 1:
                                self.BookBlock(i[0],i[1],i[2]-1, name)
                                coun -= i[2] -1
                            elif coun -i[2] <= 0:
                                self.BookBlock(i[0],i[1],coun, name)
                        return True
                    elif ans.upper() == "N" or ans.upper() == "No":
                        print "I'm sorry, but a consecutive block of " + str(coun) + " seats is not available. \nPlease try again."
                        return False
                    else:
                        print "I'm sorry, that's not a valid entry."
        return True


    def SortPrefer(self, choice):
        choice.sort(key=lambda x: x[0])
        return choice


    # If distances are equal then choose best combination based on total of row numbers
    def ChooseBestCombo(self, combs, p):
        choice = combs[p[0][0]]
        if len(p) ==1:
            return choice
        total = sum(s[0] for s in choice)
        for i in p:
            if sum(s[0] for s in combs[i[0]]) < total:
                total = sum(s[0] for s in combs[i[0]])
                choice = combs[i[0]]
        return choice


    # Creates a list of those seats with the minimum distance.
    def MinSeatDist(self, minRowCombs):
        minDist = minRowCombs[0][2]
        p = []
        for i in minRowCombs:
            if i[2]< minDist:
                p=[]
                minDist = i[2]
                p.append(i)
            elif i[2] == minDist:
                p.append(i)
        return p


    #Print a map of what seats are booked and what seats aren't
    def PrintMap(self):
        print ""
        print ""
        for i in range(self.num_rows):
            print self.rows[self.num_rows - 1 - i]
        print ""
        print "Where each 0 is an available seat, and each 1 is taken."
        print ""
        return True


    def PrintBookedSeats(self,name):
        print "You have booked seats:"
        if len(self.booker[name][1]) > 0:
            for i in self.booker[name][1]:
                print i
        else:
            print "This user has not booked any seats yet."
        return True


    def __reduce__(self):
        return (self.__class__, (self.num_rows, self.num_seats, self.rows, self.booker))


# Creates the ui
class TicketBooker:
    def __init__(self):
        print "Welcome to the venue build and book system... \n"
        self.MenuSelect()
        self.fileName = ""


    # A more robust way of asking for an integer input
    def GetIntInput(self, message):
        try:
            val = int(raw_input(message))
        except ValueError:
            print "That is not an integer, please try again."
            return False
        return val

    def OpenVenue(self,venueName):
        filename = str(venueName)
        try: 
            ven = open(filename, "rb")
        except IOError:
            return False
        ven.close()
        ven = open(filename, "rb")
        print "Venue has been opened"
        return ven

    def LoadVenue(self, venFile):
        print "Trying to load"
        venInfo = pickle.load(venFile)
        venInfo = venInfo[1]
        self.v = Venue(venInfo[0],venInfo[1],venInfo[2],venInfo[3])
        print "Printing map...\n"
        self.v.PrintMap()
        return True

    # Builds the front end
    def MenuSelect(self):
        ans = raw_input('Would you like to use an existing Venue? ')
        if ans.upper() == 'Y' or ans.upper() == 'YES':
            self.fileName = self.NameVenue()
            venFile = self.OpenVenue(self.fileName)
            if type(venFile) is bool:
                print "I'm sorry but that file doesn't seem to exist."
                self.MenuSelect()
                return True
            else:
                self.LoadVenue(venFile)
                venFile.close()
        elif ans.upper() == 'N' or ans.upper() == 'NO':
            self.fileName = self.NameVenue()
            venFile = self.OpenVenue(self.fileName)
            if type(venFile) is bool:
                rows = 0
                while (type(rows) is not int) or rows <1:
                    rows = self.GetIntInput("Please enter the number of rows in your venue: \n")

                print ""

                cols = 0
                while type(cols) is not int or cols<1:
                    cols = self.GetIntInput("Please enter the number of seats per row in your venue: \n")

                self.MakeVenue(rows, cols)
            else:
                print "I'm sorry, but it seems that that venue already exists."
                self.MenuSelect()
                return True
        else:
            print "I'm sorry, but I don't understand."
            self.MenuSelect()
            return True

        self.PrintMenu()
        # Asks the user for their choice.
        choosing = self.Choose()
        # Loops so long as the user wants to book seats
        while choosing == True:
            pickle.dump(self.v.__reduce__(), open(self.fileName, "wb"))
            print ""
            self.PrintMenu()
            choosing = self.Choose()
        time.sleep(3)
        quit

        return True
        

    def PrintMenu(self):
        print "Please select from the following options:"
        print "--------------------------------------------------"
        print "1: Book a manually selected block of rows"
        print "2: Book the best n seats"
        print "3: Create a new venue instead"
        print "4: Check booked seats"
        print "5: Exit"
        print ""
        return True

    def CheckSeats(self):
        print "You need to login."
        name = raw_input("Please enter your username: ")
        password = getpass.getpass("Please enter your password: ")
        if self.v.LoginUser(name,password):
            self.v.PrintBookedSeats(name)
            return True
        else:
            print "\nPlease try again.\n"
            return False


    def Choose(self):
        selection = self.GetIntInput("Input: ")
        while type(selection) is not int or selection <1 or selection > 5 :
            selection = self.GetIntInput("That selection is not valid. \nPlease try again: ")        
        if selection == 1:
            self.SelectBlock()
            return True
        elif selection  == 2:
            self.BestSeats()
            return True
        elif selection == 3:
            print "Current Venue saved as " + str(self.fileName)
            pickle.dump(self.v.__reduce__(), open(self.fileName, "wb"))
            self.MenuSelect()
            return True
        elif selection == 5:
            print "Current Venue saved as " + str(self.fileName)
            pickle.dump(self.v.__reduce__(), open(self.fileName, "wb"))
            print "Thank you for using our software."
            return False
        elif selection == 4:
            self.CheckSeats()
            return True
        else:
            print "I'm sorry but I don't understand... Please try again or enter 4 at any time to exit."
            return True

    def UserControl(self):
        while True:
            if len(self.v.booker) >0:
                ans = raw_input("Would you like to book under an existing username? ")
            else:
                ans = 'N'
            if ans.upper() == 'Y' or ans.upper() == 'YES':
                loginDetails = self.LoginScreen()
                if self.v.LoginUser(loginDetails[0], loginDetails[1]):
                    print "You are logged in as " + str(loginDetails[0]) + "."
                    return loginDetails[0]
                else:
                    print "Sorry that didn't work."
                    ans = raw_input("Would you like to try again? ")
                    if ans.upper() == 'N' or ans.upper() == 'NO':
                        print "Returning to menu."
                        return False
                    elif ans.upper() == 'Y' or ans.upper() == 'YES':
                        print "Okay."
                    else:
                        print "I'm sorry, but I don't understand."
            elif ans.upper() == 'N' or ans.upper() == 'NO':
                print "You'll have to create a user account to book seats."
                loginDetails = self.LoginScreen('y')
                if self.v.CreateUser(loginDetails[0], loginDetails[1]):
                    print "Thank you."
                    return loginDetails[0]
                else:
                    print "Sorry that didn't work."
                    ans = raw_input("Would you like to try again? ")
                    if ans.upper() == 'N' or ans.upper() == 'NO':
                        print "Returning to menu."
                        return False
                    elif ans.upper() == 'Y' or ans.upper() == 'YES':
                        print "Okay."
                    else:
                        print "I'm sorry, but I don't understand."
            else:
                print "I'm sorry, but I don't understand."


    def LoginScreen(self, new='n'):
        validChar = ['a', 'b', 'c','d','e','f','g','h','i','j','k','l',
                    'm','n','o','p','q','r','s','t','u','v','w','x','y','z']
        validNum = ['0','1','2','3','4','5','6','7','8','9']
        validSym = ['_', '-', '.']
        while True:
            print "Please enter your username and password: \n"
            name = raw_input("Username: ")
            if new.lower() == 'y':
                password1 = getpass.getpass("Please enter your password: ")
                password2 = getpass.getpass("Please retype your password: ")
                while True:
                    if password1 == password2:
                        password = password1
                        break
                    else:
                        print "I'm sorry, but those passwords don't match."
                        password1 = getpass.getpass("Please enter your password: ")
                        password2 = getpass.getpass("Please retype your password: ")
            else:
                password = getpass.getpass()
            esc = 0
            for i in name:
                if validChar.count(i.lower()) ==0:
                    if validNum.count(i) ==0:
                        if validSym.count(i) ==0:
                            print "Please only use characters A-Z, a-z, 0-9 or symbols ., _, -."
                            esc = 1
                            break
            for i in password:
                if validChar.count(i.lower()) ==0:
                    if validNum.count(i) ==0:
                        if validSym.count(i) ==0:
                            print "Please only use characters A-Z, a-z, 0-9 or symbols ., _, -."
                            esc = 1
                            break
            if esc ==0:
                return [name, password]

    def NameVenue(self):
        validChar = ['a', 'b', 'c','d','e','f','g','h','i','j','k','l',
                    'm','n','o','p','q','r','s','t','u','v','w','x','y','z']
        validNum = ['0','1','2','3','4','5','6','7','8','9']
        validSym = ['_', '-', '.', ' ', '\'']
        while True:
            print "Please enter the venue name: \n"
            name = raw_input("Venue Name: ")
            esc = 0
            for i in name:
                if validChar.count(i.lower()) ==0:
                    if validNum.count(i) ==0:
                        if validSym.count(i) ==0:
                            print "Please only use characters A-Z, a-z, 0-9 or symbols ., _, -."
                            esc = 1
                            break
            if esc == 0:
                name = str(name) + ".txt"
                return name

    # Creates a venue
    def MakeVenue(self, no_rows, no_seats):
        self.v = Venue(no_rows, no_seats)
        self.v.PrintMap()
        return True

    # Books a select block
    def SelectBlock(self):
        name = self.UserControl()
        if type(name) is not str:
            print "You need to login to book seats."
            return False

        row = self.GetIntInput("Which row would you like to sit on? ")

        # Checks that input is valid
        while row<1:
            row = self.GetIntInput("Which row from 1 to " + str(self.v.num_rows) + " would you like to sit on? ")

        seat_start = self.GetIntInput("Which seat would you like the block to start on?")

        # Checks that input is valid
        while type(seat_start) is not int and seat_start<1:
            print "I'm sorry, but I don't understand."
            seat_start = self.GetIntInput("Whhich seat from 1 to " + str(self.v.num_seats) + " would you like your block to start on? ")

        no = 0
        # Checks that the input is valid
        while type(no) is not int or no<1:
            no = self.GetIntInput("How many seats would you like to book?")

        # Tries to book the seat
        sel1 = self.v.BookSelectBlock(row, seat_start, no, name)
        
        if not sel1:
            while True:
                b = raw_input("We're sorry that didn't work out.... \n Would you like us to find the best " + str(no) + " seats?")
                if b.upper() == "Y" or b.upper() == "YES":
                    c = self.v.AnyBlockBook(no, name)
                    if not c:
                        print "We're very sorry, please try again."
                        return False
                    else:
                        self.v.PrintMap()
                        return True
                elif b.upper() == "N" or b.upper() == "NO":
                    print "Thank you."
                    return False
                else:
                    print "I'm sorry, but I don't understand. Please enter (yes) or (n)o. \n"
        else:
            self.v.PrintMap()
            return True

    # Books the best seats available
    def BestSeats(self):
        name = self.UserControl()
        if type(name) is not str:
            print "You need to login to book seats."
            return False
        g = False
        while not g:
            no = 0
            while type(no) is not int or no<1:
                no = self.GetIntInput("How many seats would you like to book today? ")
            g = self.v.AnyBlockBook(no, name)
            if not g:
                h = ""
                while True:
                    h = str(raw_input("Would you like to try again? y or n?"))
                    if h.upper() == "Y" or h.upper() == "YES":
                        print ""
                        break
                    elif h.upper() == "N" or h.upper() == "NO":
                        print "Thank you."
                        return False
                    else:
                        print "I'm sorry, but I don't understand."
            if g:
                self.v.PrintMap()
                return True

    # Starts again and makes a new venue.
    def NewVenue(self):
        self.MenuSelect()
        return True
        


if __name__ == "__main__":
    start = TicketBooker()
    
