
# Author: Ramirez22
#
"""
<plugin key="KinCony_KC868" name="KinCony KC868 plugin" author="Ramirez22" version="1.0.0" 
externallink="https://www.kincony.com/product/relay-controller">
    <description>
        <h2>KinCony KC868</h2><br/>
        TCP input/output card <br/>
        <br/>
        <h3>Functionality</h3>
        <ul style="list-style-type:square">
             <li> Creation of switches according to the selected card (activatable relays and read-only inputs) </li>
             <li> Initialization and dialogue with the card </li>
             <li> Refreshing the display after each command </li>
             <li> Polling of inputs with adjustable frequency </li>
        </ul>
        <h3>Device selection</h3>
        <ul style="list-style-type:square">
            <li>HC868-H32 - 32 outputs, 6 inputs</li>        
            <li>HC868-H16 - 16 outputs, 8 inputs</li>
            <li>HC868-H4  -  4 outputs, 4 inputs</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Adresse IP / Port</li>
        </ul>
        Enter the address of the slave device as well as the communication port (default is 4196) <br/>
        <br/>
        <ul style="list-style-type:square">
            <li>Mode</li>
        </ul>
        Choose mode of the card <br/>
        <br/>
        <ul style="list-style-type:square">
            <li> Reset output on creation / update / exit / deactivation </li>
        </ul>
        Reset all outputs on creation, update, deletion or deactivation <br/>
        <br/>
        <ul style="list-style-type:square">
            <li> Number of virtual devices </li>
        </ul>
       Creation of virtual devices. It is possible to place orders directly via the 'description' field of the device. The possible commands are: <br/>
         - RELAY-SET_ALL-1, Byte3, Byte2, Byte1, Byte0 (cards with 32 outputs) <br/>
         - RELAY-SET_ALL-1, Byte1, Byte0 (cards with 16 outputs) <br/>
         - RELAY-SET_ALL-1, Byte0 (cards with 8 outputs and less) <br/>
         - RELAY-SET_ONLY, Mask3, Octet3, Mask2, Octet2, Mask1, Octet1, Mask0, Octet0 (cards with 32 outputs) <br/>
         - RELAY-SET_ONLY, Mask1, Octet1, Mask0, Octet0 (cards with 16 outputs) <br/>
         - RELAY-SET_ONLY, Mask0, Octet0 (cards with 8 outputs and less) <br/>
         The RELAY-SET_ALL-1 command forces all outputs to the specified decimal value (0 to 255) <br/>
         The RELAY-SET_ONLY command changes only the outputs whose mask is at 1 (0 to 255), the others outputs remain unchanged. <br/>
         <br/> 
        <ul style="list-style-type:square">
            <li> Input polling frequency </li>
        </ul>
        The higher the frequency, the faster the input capture and the faster the events can be
        captured. However, the network and CPU load increases as much ... To be adapted according to your needs. <br/>
        Link to commercial site: <a href="https://kincony.aliexpress.com/store/group/Smart-Controller/807891_259382457.html?spm=a2g0w.12010612.1000001.12.33545853zn9vxT" target="_blank">Aliexpress</a>
    </description>
    <params>
        <param field="Address" label="Address IP" width="150px" required="true" />
        <param field="Port" label="Port" width="80px" required="true" default="4196" />
        <param field="Mode1" label="Mode1" width="250px" required="true">
            <options>
                <option label="HC868-H32 (32 relays/6 inputs)" value="32 6" />
                <option label="HC868-H16 (16 relays/8 inputs)" value="16 8" />
                <option label="HC868-H4 (4 relays/4 inputs)" value="4 4" />
            </options>
        </param>
        <param field = "Mode2" label = "Reset outputs on creation / update" width = "85px" required = "true">
            <options>
                <option label="No" value="False" />
                <option label="Yes" value="True" default="true" />
            </options>
        </param>
        <param field = "Mode3" label = "Reset outputs on deletion / deactivation" width = "85px" required = "true">
            <options>
                <option label="No" value="False" />
                <option label="Yes" value="True" default="true" />
            </options>
        </param>
        <param field="Mode4" label="Number of virtual devices" width="85px"  default="0"/>
        <param field = "Mode5" label = "Input polling frequency" width = "250px" required = "true">
            <options>
                <option label="5 times per second (200 ms)" value="2" />
                <option label="4 times per second (250 ms)" value="3" default="true" />
                <option label = "Approx. 3 times per second (300 ms)" value = "4" />
                <option label="2 times per second (500 ms)" value="8" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="85px">
            <options>
                <option label = "Enabled" value = "True" />
                <option label = "Silent" value = "False" default = "true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import os, sys
import socket
import time
import threading
import select
from math import ceil

debug = False

class BasePlugin:

    def __init__(self):
        # ~ self.connexion_TCP = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # ~ self.connexion_TCP.settimeout(1)
        self.checkInputs = threading.Thread(name="ThreadCheckInputs", target = BasePlugin.KinconyCheckInputs, args=(self,))
        return


    def onStart(self):
        """
        Called to the creation of the material
        Creation of input and output devices + launch of communication
        """
        global debug
        # Miscellaneous variables and parameters
        self.host = Parameters["Address"]
        self.port = int(Parameters["Port"])
        # ~ self.heartbeat_count = 1
        # ~ self.HEARTBEAT_MAX = 3
        self.nb_sorties, self.nb_entrees = (int(x) for x in Parameters["Mode1"].split())
        self.connexion_ok = False
        # Log
        if Parameters["Mode6"] == "True":
            debug = True
        else:
            debug = False
        Debug("onStart call")
        # Creation of devices (if necessary)
        if (len(Devices) == 0):
            Debug ("onStart - Creating devices. Number of inputs:" + str (self.nb_entrees) + ", number of outputs:" + str (self.nb_sorties))

            # Outputs
            for sortie in range(1, self.nb_sorties + 1):
                Domoticz.Device(Unit=sortie, Name="Relais " + str(sortie), TypeName="Switch", Used=1).Create()
            # Input
            for entree in range(1, self.nb_entrees + 1):
                Domoticz.Device(Unit=(entree+32), Name="Entree " + str(entree), Type=244, Subtype=73, Switchtype=2, Used=1).Create()
            # If there are "virtual" devices
            Nb_dispositifs_virtuels = int(Parameters["Mode4"])
            if Nb_dispositifs_virtuels > 0:
                Debug ("onStart - Creation of" + str (Nb_dispositifs_virtuels) + "virtual devices")
                for virtuel in range(1, Nb_dispositifs_virtuels + 1):
                    Domoticz.Device(Unit=(virtuel+64), Name="Virtual " + str(virtuel), Type=244, Subtype=73, Switchtype=9, Used=1).Create()
        if debug:
            DumpConfigToLog()
        self.connexion_ok = self.KinconyConnexion()
         # ~ # Connection with the card
         # ~ self.connexion_TCP.connect ((self.host, self.port)) 
         # ~ Debug ("onStart - Attempt to connect with Kincony IP card:" + self.host)
         # ~ msg_recu = self.KinconyScan ()
         # ~ if ("RELAY-SCAN_DEVICE-CHANNEL_" in msg_recu) and (", OK" in msg_recu):
             # ~ Debug ("onStart - Slave present, communication attempt")
            # ~ msg_recu = self.KinconyTest ()
            # ~ if ("OK" in msg_recu):
                # ~ Domoticz.Status ("onStart - Communication OK with the Kincony IP card:" + self.host)
            # ~ else:
                # ~ Domoticz.Error ("onStart - Communication error: '" + msg_recu + "'")
                # ~ return
         # ~ else:
             # ~ Domoticz.Error ("onStart - Communication error: '" + msg_recu + "'")
             # ~ return
         # Reset outputs on connection
        if self.connexion_ok:
            if Parameters["Mode2"] == "True":
                Debug ("onStart - Reset outputs to zero")
                valeurs_sorties = list()
                if self.nb_sorties == 32:
                    valeurs_sorties = (0,0,0,0)
                elif self.nb_sorties == 16:
                    valeurs_sorties = (0,0)
                else:
                    valeurs_sorties.append(0)
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            self.UpdateDomoticz(True, True)
            # Surveillance des entrC)es
            self.stop_thread = False
            self.checkInputs.start()


    def onStop(self):
        # Log
        Debug("onStop called")
        # List of current threads
        for thread in threading.enumerate():
            Debug ("onStop - The thread '" + thread.name + "' is still active")
        # Closing the thread
        self.stop_thread = True
        Debug ("onStop - Send the command to stop the thread")
         # Wait for threads to be closed
        while (threading.active_count() > 1):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name):
                  Domoticz.Log ("onStop - '" + thread.name + "' is still running. Waiting for thread to end")  
            time.sleep(1.0)
        # Reset outputs to zero on deletion?        
        if self.connexion_ok:
            if Parameters["Mode3"] == "True":
                Debug ("onStop - Reset outputs to zero")                
                valeurs_sorties = list()
                if self.nb_sorties == 32:
                    valeurs_sorties = (0,0,0,0)
                elif self.nb_sorties == 16:
                    valeurs_sorties = (0,0)
                else:
                    valeurs_sorties.append(0)
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            self.UpdateDomoticz(True, True)
            # Close the socket            
            self.connexion_TCP.close()
        
        
    def onCommand(self, Unit, Command, Level, Hue):
        """
         Called each time a Device is changed. If the device in question is a
         virtual type (n > 64), reading of the command passed in Description of the Device.
         The values are integers (between 0 and 255, corresponding to the value of an 8-bit word)
         - RELAY-SET_ALL-1, ... standard operation of a command of this type
         - RELAY-SET_ONLY, <mask>, <value>, ... the mask allows not to modify the bits to 0
           (they will keep their state).
        """        
        # Log
        Debug ("onCommand called. Unit:" + str (Unit) + ": Parameter '" + str (Command) + "', Level:" + str (Level) + ", Hue:" + str (Hue))
        # If the connection is not active, return
        if not self.connexion_ok:
            Domoticz.Error ("Command impossible, lost connection to card")
            return
        # If the connection is OK, stop the entry verification thread
        self.stop_thread = True
        self.checkInputs.join()
        # Control of outputs individually (outputs are systematically <= 32)
        if Unit <= 32:
            msg_recu = self.KinconyWriteOutput(str(Unit), str(Command))
        # Control of outputs by 'virtual' device
        if Unit >= 65:
            valeurs_sorties = list()
            commande = Devices[Unit].Description
            Domoticz.Log ("onCommand - Direct order:" + commande)
             # If the command is a SET-RELAY_ALL command
            if "RELAY-SET_ALL-1," in commande:
                commande = commande.replace("RELAY-SET_ALL-1,","")
                valeurs_sorties = commande.split(',')
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            # Recovery of the value of the initial outputs
            elif "RELAY-SET_ONLY," in commande:
                valeurs_initiales = list()
                valeurs_demandees = list()
                masque = list()
                temp = list()
                # Recovery of the value of the initial outputs
                msg_recu = self.KinconyReadOutputs()
                valeurs_initiales = [int(i) for i in msg_recu.split(',')]
                #Debug ("onCommand - Initial values output:" + str (initial_values))
                nb_mots= len(valeurs_initiales)
                # Extraction of parameters
                commande = commande.replace("RELAY-SET_ONLY,","")
                temp = commande.split (',') # temp contains a list of x mask, y values
                 # Check if the number of parameters is correct and sort the parameters
                nb_param = len(temp)
                if (nb_param == 2 or nb_param == 4 or nb_param == 8) and nb_param//2 == nb_mots:
                    for i in range(0,nb_param,2):
                        masque.append(int(temp[i]))
                        valeurs_demandees.append(int(temp[i+1]))
                else:
                    Domoticz.Error ("onCommand - Error: number of parameters passed to" + Devices[Unit].Name + "incorrect")
                    return
                 # Calculation of the modifications to be made to the outputs
                for i in range(0,nb_mots):
                    valeurs_sorties.append((masque[i] & valeurs_demandees[i]) | (~masque[i] & valeurs_initiales[i]))
                Debug ("onCommand - Calculated output values:" + str (valeurs_sorties))                
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            else:
                Debug ("onCommand - Unknown command passed to" + Devices[Unit].Name)
         # Update of Domoticz
        self.UpdateDomoticz(False, True)
        # Restarting the input monitoring thread
        self.stop_thread = False
        self.checkInputs = threading.Thread(name="ThreadCheckInputs", target = BasePlugin.KinconyCheckInputs, args=(self,))
        self.checkInputs.start()


    def onHeartbeat (self):
         """
          Regular call to test if the input polling thread is still active
          The revival if this is not the case
         """
         # Log
         Debug ("onHeartbeat called")
         if not self.connexion_ok:
             self.connexion_ok = self.KinconyConnexion ()
         if not self.connexion_ok:
             return
         # Checking the activation of the input status checking thread
         if not self.checkInputs.is_alive ():
             # List of current threads
             for thread in threading.enumerate ():
                 Debug ("onHeartbeat - Active threads: '" + thread.name + "'")
             Domoticz.Error ("onHeartbeat - The thread no longer exists, attempting to restart")
             self.stop_thread = False
             self.checkInputs = threading.Thread(name="ThreadCheckInputs", target = BasePlugin.KinconyCheckInputs, args=(self,))
             self.checkInputs.start ()
           
        
    def KinconyScan(self):
        """
         Initialization of communication with the Kincony card
         Corresponds to sending the TCP frame:
         - RELAY-SCAN_DEVICE-NOW , response must contain 'OK'
        """        
        # Log
        Debug("KinconyScan - Call : 'RELAY-SCAN_DEVICE-NOW'")
        # sending frame
        KinconyTx = "RELAY-SCAN_DEVICE-NOW"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyScan - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyScan - Reply confirmation")
                continue
            elif ("RELAY-SCAN_DEVICE" in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-SCAN_DEVICE")
                end = (msg_recu.find(",OK"))+3
                Debug("KinconyScan - Reception OK :'" + msg_recu[start:end] + "'")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadInputs - Error")
                return ("ERROR")

    
    def KinconyTest(self):
        """
         Initialization of communication with the Kincony card
         Corresponds to sending the RELAY-TEST-NOW frame
         response must contain HOST-TEST-START
        """
        # Log
        Debug("KinconyTest - Call : 'RELAY-TEST-NOW'")
        # sending frame
        KinconyTx = "RELAY-TEST-NOW"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyTest - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyScan - Reply confirmation")
                continue
            elif "HOST-TEST-START" in msg_recu:
                Debug("KinconyTest - Communication OK")
                return ("OK")
            else:
                Domoticz.Error("KinconyTest - Error : " + msg_recu)
                return("ERROR")

        
    def KinconyReadInputs(self):
        """
         Reading the card inputs. Returns the value of the byte
         input of the card if OK (as an integer), "ERROR" otherwise
        """
        # Log
        Debug("KinconyReadInputs - Call: 'RELAY-GET_INPUT-1'")
        # sending frame
        KinconyTx = "RELAY-GET_INPUT-1"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyReadInputs - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")

            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyScan - Reply confirmation")
                continue
            elif ("RELAY-GET_INPUT-1," in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-GET_INPUT-1,")
                end = msg_recu.find(",OK")
                Debug("KinconyReadInputs - Reception stat of input OK :'" + msg_recu[start:end+3] + "'")
                start = start + len("RELAY-GET_INPUT-1,")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadInputs - Error '" + msg_recu + "'")
                return ("ERROR")


    def KinconyReadOutputs(self):
        """
         Reading outputs of the card. Returns the value of each output byte
         of the card (integer, in the form byte3, byte2, byte1, byte0 for a card with 
         32 outputs, byte1, byte0 for a card with 16 outputs, byte0 for the cards
         with 8 outputs and less) if OK, otherwise "ERROR"
        """
        # Log
        Debug("KinconyReadOutputs - Call : 'RELAY-STATE-1'")
        # sending frame
        KinconyTx = "RELAY-STATE-1"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyReadOutputs - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug("KinconyReadOutputs - Reply confirmation")
                continue
            elif ("RELAY-STATE-1," in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-STATE-1,")
                end = msg_recu.find(",OK")
                Debug("KinconyReadInputs - Reception stat of input OK :'" + msg_recu[start:end+3] + "'")
                start = start + len("RELAY-STATE-1,")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadOutputs - Error '" + msg_recu + "'")
                return ("ERROR")
        
        
    def KinconyWriteOutput(self, Output, Value):
        """
        Writing an output from the card.
         Parameters: Output: integer corresponding to number of active output
                      Value: 0 or 1
         Returns "OK" if everything went well,  ERROR otherwise
        """
        # Log
        #Debug("KinconyWriteOutput - Call")
        # sending frame
        KinconyTx = "RELAY-SET-1," + Output + "," + ("1" if Value == "On" else "0")
        Debug("KinconyWriteOutput - Sending :'" + KinconyTx + "'")
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyWriteOutput - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str (msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyWriteOutput - Reply confirmation")
                continue
            elif ("RELAY-SET-1," in msg_recu) and (",OK" in msg_recu):
                Debug("KinconyWriteOutput - Output control OK")
                return("OK")
            else:
                Domoticz.Error("KinconyWriteOutput - Error")
                return ("ERROR")
        
        
    def KinconyWriteAllOutputs(self, *Value):
        """
        Write all the outputs of the card.
         Passed values are  in decimal corresponding the binary value of a byte (0 - 255)
         - If 32 outputs: 4 bytes in the order 4, 3, 2, 1
         - If 16 outputs: 2 bytes in order 2, 1
         - If 8, 4 or 2 outputs: 1 single byte
        """
        # Parameter consistency check / number of output words of the card (number of outputs / 8. If < 8 ) result must be equal to 1)        
        if len(Value) != ceil(self.nb_sorties / 8):
            Domoticz.Error ("KinconyWriteAllOutputs - Error: number of inconsistent parameters")
            return
        # Calculation of values to transmit
        KinconyTx = "RELAY-SET_ALL-1,"
        for i in range(0,len(Value)):
            KinconyTx = KinconyTx + str(Value[i]) + ","
        KinconyTx = KinconyTx[:-1]
        Debug("KinconyWriteAllOutputs - Sending : '" + KinconyTx + "'")
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Read the return message, restart if the message corresponds to change of the ALARM state of an input
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error ("KinconyScan - Communication error")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyWriteAllOutputs - Error :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str (msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyWriteAllOutputs - Reply confirmation")
                continue
            elif ("RELAY-SET_ALL-1," in msg_recu) and (",OK" in msg_recu):
                Debug("KinconyWriteAllOutputs -Output control OK")
                return("OK")
            else:
                Domoticz.Error("KinconyWriteAllOutputs - Error")
                return ("ERROR")


    def UpdateDomoticz(self, Inputs, Outputs):
        """
        Update of the input / output status of the interface in Domoticz
        Accepts as a parameter 2 boolean values to check the inputs and / or the outputs
        """
        # Log
        Debug ("UpdateDomoticz - Call my inputs =" + ("yes" if Inputs else "No") + "My outputs =" + ("yes" if Outputs else "No") + ")")
        if Inputs:
            # Updating entries
            msg_recu = self.KinconyReadInputs()
            # GET input processing (reading input and Domoticz update)
            if ("ERROR" in msg_recu):
                Domoticz.Error ("UpdateDomoticz - Error receiving input state: '" + msg_recu + "'")
                return
            Debug ("UpdateDomoticz - Receiving input state - OK: '" + msg_recu + "'")
            # binary transformation and bit inversion (^ 255), removal of '0b' ([2:]
            # and complete the word with 0's to obtain an 8-bit word (zfill (8))            
            etat_entrees = bin(int(msg_recu)^255)[2:].zfill(8)
            no_bit = 7
            # For each bit of the input word read, if the value differs from Domoticz, update
            for entree in range(33, self.nb_entrees + 33):
                if Devices[int(entree)].nValue != int(etat_entrees[no_bit]):
                    Domoticz.Status("Input " + str(entree) + " ('" + Devices[int(entree)].Name + "') " + str(etat_entrees[no_bit]))
                    Debug ("UpdateDomoticz - Input value mismatch" + str (input) + ", update")
                    Devices[int(entree)].Update(nValue = int(etat_entrees[no_bit]), sValue = "Open" if etat_entrees[no_bit] == 1 else "Closed")
                no_bit -= 1
        # update of outputs
        if Outputs:
            msg_recu = self.KinconyReadOutputs()
            # STATE processing of outputs (reading outputs and update Domoticz)
            if ("ERROR" in msg_recu):
                Domoticz.Error ("UpdateDomoticz - Error outputs state reception: '" + msg_recu + "'")
                return
            Debug("UpdateDomoticz - Output state reception - OK : '" + msg_recu + "'")
            mots = list()
            mots = msg_recu.split(",")
            mots.reverse()
            nb_mots = len(mots)
            # Extraction of the number of words returned by the card
            if nb_mots != 1:
                for mot_en_cours in range(nb_mots):
                    etat_sorties = bin(int(mots[mot_en_cours]))[2:].zfill(8)
                    no_bit = 7
                    for sortie in range(1+(mot_en_cours*8), 9+(mot_en_cours*8)):
                        if Devices[int(sortie)].nValue != int(etat_sorties[no_bit]):
                            Debug ("UpdateDomoticz - Mismatch value output" + str (sortie) + ", update")
                            Devices[int(sortie)].Update(nValue = int(etat_sorties[no_bit]), sValue = "On" if etat_sorties[no_bit] == 1 else "Off")
                        no_bit -= 1
            else:
                etat_sorties = bin(int(mots[0]))[2:].zfill(8)
                no_bit = 7
                for sortie in range(1, self.nb_sorties+1):
                    if Devices[int(sortie)].nValue != int(etat_sorties[no_bit]):
                        Debug ("UpdateDomoticz - Mismatch value output" + str (sortie) + ", update")
                        Devices[int(sortie)].Update(nValue = int(etat_sorties[no_bit]), sValue = "On" if etat_sorties[no_bit] == 1 else "Off")
                    no_bit -= 1
                

    def KinconyCheckInputs(self):
        """
        Verification of entries.
        The loop at the end of the check makes it possible to interrupt the cycle more quickly if a command
        control output is received (onCommand). The input scanning frequency is configurable
        in the plugin options.
        """
        Debug("KinconyCheckInputs - Thread launch")
        self.frequence_check = int(Parameters["Mode5"])
        Debug ("Frequency refresh rate:" + str (int (self.frequence_check) * 50) + "ms + cycle time of about 100 ms")
        while not self.stop_thread:
            self.UpdateDomoticz(True, False)
            for i in range(0,self.frequence_check):
                time.sleep(0.05)
                if self.stop_thread:
                    break
        Debug("KinconyCheckInputs - thread stop")


    def KinconyConnexion(self):
        # Connection with card
        self.connexion_TCP = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connexion_TCP.settimeout(2)

        try:
            self.connexion_TCP.connect((self.host,self.port))
        except socket.timeout:
            Domoticz.Error ("KinconyConnexion - Communication error")
            self.connexion_TCP.close()
            return False
        except Exception as err:
            Domoticz.Error("KinconyConnexion - Error :" + str(err))
            self.connexion_TCP.close()
            return False
        Debug ("KinconyConnexion - Attempt to connect with the Kincony IP card:" + self.host)
        msg_recu = self.KinconyScan()
        if ("RELAY-SCAN_DEVICE-CHANNEL_" in msg_recu) and (",OK" in msg_recu):
            Debug ("onStart - Slave present, communication attempt")
            msg_recu = self.KinconyTest()
            if ("OK" in msg_recu):
                Domoticz.Status ("KinconyConnexion - Communication OK with the Kincony IP card:" + self.host)
                return True
            else:
                Domoticz.Error("KinconyConnexion - Communication error: '" + msg_recu + "'")
                return False
        else:
            Domoticz.Error("KinconyConnexion - Communication error: '" + msg_recu + "'")
            return False


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    ## Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def Debug(text):
    global debug
    if (debug):
        Domoticz.Log(text)
