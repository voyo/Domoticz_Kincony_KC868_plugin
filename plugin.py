#
# Author: Ramirez22
#
"""
<plugin key="KinCony_KC868" name="KinCony KC868 plugin" author="Ramirez22" version="1.0.0" 
externallink="https://www.kincony.com/product/relay-controller">
    <description>
        <h2>KinCony KC868</h2><br/>
        Carte d'entrées/sorties sur protocole TCP<br/>
        <br/>
        <h3>Fonctionnalités</h3>
        <ul style="list-style-type:square">
            <li>Création des interrupteurs en fonction de la carte selectionnée (relais activables et entrées en lecture seule)</li>
            <li>Initialisation et dialogue avec la carte</li>
            <li>Raffraichissement de l'affichage après chaque commande</li>
            <li>Scrutation des entrées avec fréquence réglable</li>
        </ul>
        <h3>Modèles supportés</h3>
        <ul style="list-style-type:square">
            <li>HC868-H16 - 16 sorties, 8 entrées</li>
            <li>HC868-H4  -  4 sorties, 4 entrées</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Adresse IP / Port</li>
        </ul>
        Saisir l'adresse du dispositif esclave ainsi que le port de communication (par défaut 4196)<br/>
        <br/>
        <ul style="list-style-type:square">
            <li>Modèle</li>
        </ul>
        Choisir le modèle de carte<br/>
        <br/>
        <ul style="list-style-type:square">
            <li>RAZsortie à la création / mise à jour / sortie / désactivation</li>
        </ul>
        Remise à zéro de toutes les sorties à la création, à la mise à jour, lors de la suppression ou de la désactivation<br/>
        <br/>
        <ul style="list-style-type:square">
            <li>Nb de dispositifs virtuels</li>
        </ul>
        Création de dispositifs virtuels. Il est possible de passer diretement des commandes via le champ 'description' du 
        dispositif. Les commandes possibles sont:<br/>
        - RELAY-SET_ALL-1,Octet3,Octet2,Octet1,Octet0 (cartes avec 32 sorties)<br/>
        - RELAY-SET_ALL-1,Octet1,Octet0 (cartes avec 16 sorties)<br/>
        - RELAY-SET_ALL-1,Octet0 (cartes avec 8 sorties et moins)<br/>
        - RELAY-SET_ONLY,Mask3,Octet3,Mask2,Octet2,Mask1,Octet1,Mask0,Octet0 (cartes avec 32 sorties)<br/>
        - RELAY-SET_ONLY,Mask1,Octet1,Mask0,Octet0 (cartes avec 16 sorties)<br/>
        - RELAY-SET_ONLY,Mask0,Octet0 (cartes avec 8 sorties et moins)<br/>
        La commande RELAY-SET_ALL-1 force toutes les sorties à la valeur décimale spécifiée (0 à 255)<br/>
        La commande RELAY-SET_ONLY, change uniquement les sorties dont le mask est à 1 (0 à 255), les autres 
        sorties restent inchangées.<br/>
        <br/>
        <ul style="list-style-type:square">
            <li>Fréquence de scrutation des entrées</li>
        </ul>
        Plus la fréquence est élevée, plus la capture des entrées est rapide et plus les évènements rapides peuvent être 
        capturés. Cependant, la charge du réseau et du CPU augmente d'autant... A adapter en fonction de vos besoins.<br/>
        <br/>
        Lien vers un site commercial : <a href="https://kincony.aliexpress.com/store/group/Smart-Controller/807891_259382457.html?spm=a2g0w.12010612.1000001.12.33545853zn9vxT" target="_blank">Aliexpress</a>
    </description>
    <params>
        <param field="Address" label="Adresse IP" width="150px" required="true" />
        <param field="Port" label="Port" width="80px" required="true" default="4196" />
        <param field="Mode1" label="Modèle" width="250px" required="true">
            <options>
                <option label="HC868-H16 (16 sorties/8 entrées)" value="16 8" />
                <option label="HC868-H4 (4 sorties/4 entrées)" value="4 4" />
            </options>
        </param>
        <param field="Mode2" label="RAZ sorties à la création/mise à jour" width="85px" required="true">
            <options>
                <option label="Non" value="False" />
                <option label="Oui" value="True" default="true" />
            </options>
        </param>
        <param field="Mode3" label="RAZ sorties à la suppression/désactivation" width="85px" required="true">
            <options>
                <option label="Non" value="False" />
                <option label="Oui" value="True" default="true" />
            </options>
        </param>
        <param field="Mode4" label="Nb de dispositifs virtuels" width="85px"  default="0"/>
        <param field="Mode5" label="Fréquence de scrutation des entrées" width="250px" required="true">
            <options>
                <option label="5 fois par secondes (200 ms)" value="2" />
                <option label="4 fois par secondes (250 ms)" value="3" default="true" />
                <option label="Env. 3 fois par secondes (300 ms)" value="4" />
                <option label="2 fois par secondes (500 ms)" value="8" />
            </options>
        </param>
        <param field="Mode6" label="Debug" width="85px">
            <options>
                <option label="Activé" value="True" />
                <option label="Silencieux" value="False" default="true" />
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
        Appelée à la création du matériel
        Création des dispositifs d'entrées et de sorties + lancement de la communication
        """
        global debug
        # Variables et paramètres divers
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
        Debug("onStart appelé")
        # Création des dispositifs (si besoin) 
        if (len(Devices) == 0):
            Debug("onStart - Création dispositifs. Nombre d'entrées : " + str(self.nb_entrees) + ", nombre de sorties : " + str(self.nb_sorties))
            # Sorties
            for sortie in range(1, self.nb_sorties + 1):
                Domoticz.Device(Unit=sortie, Name="Relais " + str(sortie), TypeName="Switch", Used=1).Create()
            # Entrées
            for entree in range(1, self.nb_entrees + 1):
                Domoticz.Device(Unit=(entree+32), Name="Entree " + str(entree), Type=244, Subtype=73, Switchtype=2, Used=1).Create()
            # S'il y a des dispositifs "virtuels"
            Nb_dispositifs_virtuels = int(Parameters["Mode4"])
            if Nb_dispositifs_virtuels > 0:
                Debug("onStart - Création de " + str(Nb_dispositifs_virtuels) + " dispositifs virtuels")
                for virtuel in range(1, Nb_dispositifs_virtuels + 1):
                    Domoticz.Device(Unit=(virtuel+64), Name="Virtuel " + str(virtuel), Type=244, Subtype=73, Switchtype=9, Used=1).Create()
        if debug:
            DumpConfigToLog()
        self.connexion_ok = self.KinconyConnexion()
        # ~ # Connexion avec la carte
        # ~ self.connexion_TCP.connect((self.host,self.port))
        # ~ Debug("onStart - Tentative de connexion avec la carte Kincony IP:" + self.host)
        # ~ msg_recu = self.KinconyScan()
        # ~ if ("RELAY-SCAN_DEVICE-CHANNEL_" in msg_recu) and (",OK" in msg_recu):
            # ~ Debug("onStart - Esclave présent, tentative de communication")
            # ~ msg_recu = self.KinconyTest()
            # ~ if ("OK" in msg_recu):
                # ~ Domoticz.Status("onStart - Communication OK avec la carte Kincony IP:" + self.host)
            # ~ else:
                # ~ Domoticz.Error("onStart - Erreur de communication: '" + msg_recu + "'")
                # ~ return
        # ~ else:
            # ~ Domoticz.Error("onStart - Erreur de communication: '" + msg_recu + "'")
            # ~ return
        # Remise à zéro des sorties à la connexion
        if self.connexion_ok:
            if Parameters["Mode2"] == "True":
                Debug("onStart - Remise à zéro des sorties")
                valeurs_sorties = list()
                if self.nb_sorties == 32:
                    valeurs_sorties = (0,0,0,0)
                elif self.nb_sorties == 16:
                    valeurs_sorties = (0,0)
                else:
                    valeurs_sorties.append(0)
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            self.UpdateDomoticz(True, True)
            # Surveillance des entrées
            self.stop_thread = False
            self.checkInputs.start()


    def onStop(self):
        # Log
        Debug("onStop appelé")
        # Liste des threads en cours
        for thread in threading.enumerate():
            Debug("onStop - Le thread '" + thread.name + "' est toujours actif")
        # Fermeture du thread
        self.stop_thread = True
        Debug("onStop - Envoi de la commande d'arrêt du thread")
        # Attente que les thread soient fermés
        while (threading.active_count() > 1):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name):
                    Domoticz.Log("onStop - '"+thread.name+"' est toujours en éxécution. Attente fin du thread")
            time.sleep(1.0)
        # Remise à zéro des sorties à la suppression ?
        if self.connexion_ok:
            if Parameters["Mode3"] == "True":
                Debug("onStop - Remise à zéro des sorties")
                valeurs_sorties = list()
                if self.nb_sorties == 32:
                    valeurs_sorties = (0,0,0,0)
                elif self.nb_sorties == 16:
                    valeurs_sorties = (0,0)
                else:
                    valeurs_sorties.append(0)
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            self.UpdateDomoticz(True, True)
            # Fermeture du socket
            self.connexion_TCP.close()
        
        
    def onCommand(self, Unit, Command, Level, Hue):
        """
        Appelée à chaque changement d'un Device. Si le device en question est d'un 
        type virtuel (n° > à 64), lecture de la commande passée en Description du Device.
        Les valeurs sont des entiers (entre 0 et 255, correspondant à la valeur d'un mot de 8 bits)
        - RELAY-SET_ALL-1,... fonctionnement standar d'une commande de ce type
        - RELAY-SET_ONLY,<mask>,<value>,... le masque permet de ne pas modifier les bits à 0 
          (ils conserveront leur état).
        """
        # Log
        Debug("onCommand appelé. Unit: " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level) + ", Hue:" + str(Hue))
        # Si la connexion n'est pas active, retour
        if not self.connexion_ok:
            Domoticz.Error("Commande impossible, connexion avec carte perdue")
            return
        # Si la connexion est OK, arrêt du thread de vérification des entrées
        self.stop_thread = True
        self.checkInputs.join()
        # Pilotage des sorties individuellement (les sorties sont systématiquement <= 32)
        if Unit <= 32:
            msg_recu = self.KinconyWriteOutput(str(Unit), str(Command))
        # Pilotage des sorties par device 'virtuel' 
        if Unit >= 65:
            valeurs_sorties = list()
            commande = Devices[Unit].Description
            Domoticz.Log("onCommand - Ordre direct : " + commande)
            # Si la commande est une commande de type SET-RELAY_ALL
            if "RELAY-SET_ALL-1," in commande:
                commande = commande.replace("RELAY-SET_ALL-1,","")
                valeurs_sorties = commande.split(',')
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            # Pilotage de sorties spécifiques. Données à transmettre : masque, valeur (x nombre de mots)
            elif "RELAY-SET_ONLY," in commande:
                valeurs_initiales = list()
                valeurs_demandees = list()
                masque = list()
                temp = list()
                # Récupération de la valeur des sorties initiales
                msg_recu = self.KinconyReadOutputs()
                valeurs_initiales = [int(i) for i in msg_recu.split(',')]
                #Debug("onCommand - Valeurs initiales sorties : " + str(valeurs_initiales))
                nb_mots= len(valeurs_initiales)
                # Extraction des paramètres
                commande = commande.replace("RELAY-SET_ONLY,","")
                temp = commande.split(',')  # temp contient une liste de x masque, y valeurs
                # Vérification si le nombre de paramètres est conforme et tri des paramètres
                nb_param = len(temp)
                if (nb_param == 2 or nb_param == 4 or nb_param == 8) and nb_param//2 == nb_mots:
                    for i in range(0,nb_param,2):
                        masque.append(int(temp[i]))
                        valeurs_demandees.append(int(temp[i+1]))
                else:
                    Domoticz.Error("onCommand - Erreur : nombre de paramètres passés à " + Devices[Unit].Name + " incorrect")
                    return
                # Calcul des modifications à apporter aux sorties
                for i in range(0,nb_mots):
                    valeurs_sorties.append((masque[i] & valeurs_demandees[i]) | (~masque[i] & valeurs_initiales[i]))
                Debug("onCommand - Valeurs de sorties calculées : " + str(valeurs_sorties))
                msg_recu = str(self.KinconyWriteAllOutputs(*valeurs_sorties))
            else:
                Debug("onCommand - Commande inconnue passée à " + Devices[Unit].Name)
        # Mise à jour de Domoticz
        self.UpdateDomoticz(False, True)
        # Remise en route du thread de surveillance des entrées
        self.stop_thread = False
        self.checkInputs = threading.Thread(name="ThreadCheckInputs", target = BasePlugin.KinconyCheckInputs, args=(self,))
        self.checkInputs.start()


    def onHeartbeat(self):
        """
        Appel régulier pour tester si le thread de scrutation des entrées est toujours actif
        Le relance si ce n'est pas le cas
        """
        # Log
        Debug("onHeartbeat appelé")
        if not self.connexion_ok:
            self.connexion_ok = self.KinconyConnexion()
        if not self.connexion_ok:
            return
        # Vérification de l'activation du thread de vérification de l'état des entrées
        if not self.checkInputs.is_alive():
            # Liste des threads en cours
            for thread in threading.enumerate():
                Debug("onHeartbeat - Thread actifs : '" + thread.name + "'")
            Domoticz.Error("onHeartbeat - Le thread n'existe plus, tentative de redémarrage")
            self.stop_thread = False
            self.checkInputs = threading.Thread(name="ThreadCheckInputs", target = BasePlugin.KinconyCheckInputs, args=(self,))
            self.checkInputs.start()

        
    def KinconyScan(self):
        """
        Initialisation de la communication avec la carte Kincony
        Correspond à l'envoi de la trame TCP:
        - RELAY-SCAN_DEVICE-NOW (réponse doit contenir OK)
        """
        # Log
        Debug("KinconyScan - Appel : 'RELAY-SCAN_DEVICE-NOW'")
        # Envoi trame
        KinconyTx = "RELAY-SCAN_DEVICE-NOW"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyScan - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyScan - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug("KinconyScan - relecture confirmation")
                continue
            elif ("RELAY-SCAN_DEVICE" in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-SCAN_DEVICE")
                end = (msg_recu.find(",OK"))+3
                Debug("KinconyScan - Réception OK :'" + msg_recu[start:end] + "'")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadInputs - Erreur")
                return ("ERROR")

    
    def KinconyTest(self):
        """
        Initialisation de la communication avec la carte Kincony
        Correspond à l'envoi de la trame RELAY-TEST-NOW 
        Réponse doit contenir HOST-TEST-START
        """
        # Log
        Debug("KinconyTest - Appel : 'RELAY-TEST-NOW'")
        # Envoi trame
        KinconyTx = "RELAY-TEST-NOW"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyTest - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyTest - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyTest - Relecture confirmation")
                continue
            elif "HOST-TEST-START" in msg_recu:
                Debug("KinconyTest - Communication OK")
                return ("OK")
            else:
                Domoticz.Error("KinconyTest - Erreur : " + msg_recu)
                return("ERROR")

        
    def KinconyReadInputs(self):
        """
        Lecture des entrées de la carte. Retourne la valeur de l'octet 
        d'entrée de la carte si OK (sous forme d'entier), "ERROR" sinon
        """
        # Log
        Debug("KinconyReadInputs - Appel: 'RELAY-GET_INPUT-1'")
        # Envoi trame
        KinconyTx = "RELAY-GET_INPUT-1"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyReadInputs - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyReadInputs - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")

            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug("KinconyReadInputs - relecture confirmation")
                continue
            elif ("RELAY-GET_INPUT-1," in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-GET_INPUT-1,")
                end = msg_recu.find(",OK")
                Debug("KinconyReadInputs - Réception état entrées OK :'" + msg_recu[start:end+3] + "'")
                start = start + len("RELAY-GET_INPUT-1,")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadInputs - Erreur '" + msg_recu + "'")
                return ("ERROR")


    def KinconyReadOutputs(self):
        """
        Lecture des sorties de la carte. Retourne la valeur de chaque octet de sortie
        de la carte (entier, sous la forme octet3, octet2, octet1, octet0 pour une carte
        de 32 sorties, octet1, octet0 pour une carte à 16 sorties, octet0 pour les cartes
        avec 8 sorties et moins) si OK, sinon "ERROR"
        """
        # Log
        Debug("KinconyReadOutputs - Appel : 'RELAY-STATE-1'")
        # Envoi trame
        KinconyTx = "RELAY-STATE-1"
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyReadOutputs - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyReadOutputs - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str(msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug("KinconyReadOutputs - Relecture confirmation")
                continue
            elif ("RELAY-STATE-1," in msg_recu) and (",OK" in msg_recu):
                start = msg_recu.find("RELAY-STATE-1,")
                end = msg_recu.find(",OK")
                Debug("KinconyReadOutputs - Réception état sorties OK :'" + msg_recu[start:end+3] + "'")
                start = start + len("RELAY-STATE-1,")
                return(msg_recu[start:end])
            else:
                Domoticz.Error("KinconyReadOutputs - Erreur '" + msg_recu + "'")
                return ("ERROR")
        
        
    def KinconyWriteOutput(self, Output, Value):
        """
        Ecriture d'une sortie de la carte.
        Paramètres : Output : entier correspondant au numéro de la sortie à activer
                     Value  : 0 ou 1
        Renvoie "OK" si tout s'est bien passé, ERROR dans le cas contraire
        """
        # Log
        #Debug("KinconyWriteOutput - Appel")
        # Envoi trame
        KinconyTx = "RELAY-SET-1," + Output + "," + ("1" if Value == "On" else "0")
        Debug("KinconyWriteOutput - Envoi :'" + KinconyTx + "'")
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyWriteOutput - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyWriteOutput - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str (msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyWriteOutput - Relecture confirmation")
                continue
            elif ("RELAY-SET-1," in msg_recu) and (",OK" in msg_recu):
                Debug("KinconyWriteOutput - Pilotage sortie OK")
                return("OK")
            else:
                Domoticz.Error("KinconyWriteOutput - Erreur")
                return ("ERROR")
        
        
    def KinconyWriteAllOutputs(self, *Value):
        """
        Ecriture de toutes les sorties de la carte. 
        Valeurs passées en décimal correspondant à la valeur binaire d'un octet (0 à 255)
        - Si 32 sorties : 4 octets dans l'ordre 4, 3, 2, 1
        - Si 16 sorties : 2 octets dans l'ordre 2, 1
        - Si 8, 4 ou 2 sorties : 1 seul octet
        """
        # Contrôle cohérence paramètres / nombre de mots de sorties de la carte (nombre de sorties / 8. Si < à 8, résultat doit être égal à 1)
        if len(Value) != ceil(self.nb_sorties / 8):
            Domoticz.Error("KinconyWriteAllOutputs - Erreur : nombre de paramètres incohérents")
            return
        # Calcul des valeurs à transmettre
        KinconyTx = "RELAY-SET_ALL-1,"
        for i in range(0,len(Value)):
            KinconyTx = KinconyTx + str(Value[i]) + ","
        KinconyTx = KinconyTx[:-1]
        Debug("KinconyWriteAllOutputs - Envoi : '" + KinconyTx + "'")
        self.connexion_TCP.sendto(KinconyTx.encode(), (self.host,self.port))
        # Lecture du message de retour, relance si le message correspond à une ALARM de changement d'état d'une entrée
        while True:
            try:
                msg_recu = self.connexion_TCP.recv(256)
            except socket.timeout:
                Domoticz.Error("KinconyWriteAllOutputs - Erreur de communication")
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            except Exception as err:
                Domoticz.Error("KinconyWriteAllOutputs - Erreur :" + str(err))
                self.connexion_TCP.close()
                self.connexion_ok = False
                return ("ERROR")
            msg_recu.decode()
            msg_recu = str (msg_recu)
            if "RELAY-ALARM" in msg_recu:
                Debug ("KinconyWriteAllOutputs - Relecture confirmation")
                continue
            elif ("RELAY-SET_ALL-1," in msg_recu) and (",OK" in msg_recu):
                Debug("KinconyWriteAllOutputs - Pilotage sorties OK")
                return("OK")
            else:
                Domoticz.Error("KinconyWriteAllOutputs - Erreur")
                return ("ERROR")


    def UpdateDomoticz(self, Inputs, Outputs):
        """
        Mise à jour de l'état des entrées/sorties de l'interface dans Domoticz
        Accepte en paramètre 2 valeurs booléennes pour vérifier les entrées et/ou les sorties
        """
        # Log
        Debug("UpdateDomoticz - Appel (MaJ entrées = " + ("oui" if Inputs else "Non") + " MaJ sorties = " + ("oui" if Outputs else "Non") + ")")
        if Inputs:
            # Mise à jour des entrées
            msg_recu = self.KinconyReadInputs()
            # Traitement GET entrées (lecture des entrées et mise à jour Domoticz)
            if ("ERROR" in msg_recu):
                Domoticz.Error("UpdateDomoticz - Erreur réception état entrées: '" + msg_recu + "'")
                return
            Debug("UpdateDomoticz - Réception état entrées OK :'" + msg_recu + "'")
            # transformation en binaire et inversion des bits (^255), suppression du '0b' ([2:]
            # et complétion du mot avec des 0 pour obtenir un mot de 8 bits (zfill(8))
            etat_entrees = bin(int(msg_recu)^255)[2:].zfill(8)
            no_bit = 7
            # Pour chaque bit du mot d'entrée lu, si la valeur diffère de Domoticz, mise à jour
            for entree in range(33, self.nb_entrees + 33):
                if Devices[int(entree)].nValue != int(etat_entrees[no_bit]):
                    Domoticz.Status("Entrée " + str(entree) + " ('" + Devices[int(entree)].Name + "') à " + str(etat_entrees[no_bit]))
                    Debug("UpdateDomoticz - Discordance valeur entrée " + str(entree) + ", mise à jour")
                    Devices[int(entree)].Update(nValue = int(etat_entrees[no_bit]), sValue = "Open" if etat_entrees[no_bit] == 1 else "Closed")
                no_bit -= 1
        # Mise à jour des sorties
        if Outputs:
            msg_recu = self.KinconyReadOutputs()
            # Traitement STATE des sorties (lecture des sorties et mise à jour Domoticz)
            if ("ERROR" in msg_recu):
                Domoticz.Error("UpdateDomoticz - Erreur réception état sorties: '" + msg_recu + "'")
                return
            Debug("UpdateDomoticz - Réception état sorties OK : '" + msg_recu + "'")
            mots = list()
            mots = msg_recu.split(",")
            mots.reverse()
            nb_mots = len(mots)
            # Extraction du nombre de mots renvoyés par la carte
            if nb_mots != 1:
                for mot_en_cours in range(nb_mots):
                    etat_sorties = bin(int(mots[mot_en_cours]))[2:].zfill(8)
                    no_bit = 7
                    for sortie in range(1+(mot_en_cours*8), 9+(mot_en_cours*8)):
                        if Devices[int(sortie)].nValue != int(etat_sorties[no_bit]):
                            Debug("UpdateDomoticz - Discordance valeur sortie " + str(sortie) + ", mise à jour")
                            Devices[int(sortie)].Update(nValue = int(etat_sorties[no_bit]), sValue = "On" if etat_sorties[no_bit] == 1 else "Off")
                        no_bit -= 1
            else:
                etat_sorties = bin(int(mots[0]))[2:].zfill(8)
                no_bit = 7
                for sortie in range(1, self.nb_sorties+1):
                    if Devices[int(sortie)].nValue != int(etat_sorties[no_bit]):
                        Debug("UpdateDomoticz - Discordance valeur sortie " + str(sortie) + ", mise à jour")
                        Devices[int(sortie)].Update(nValue = int(etat_sorties[no_bit]), sValue = "On" if etat_sorties[no_bit] == 1 else "Off")
                    no_bit -= 1
                

    def KinconyCheckInputs(self):
        """
        Vérification des entrées.
        La boucle à la fin de la vérification permet d'interrompre le cycle plus rapidement si une commande 
        de pilotage de sortie est reçue (onCommand). La fréquence de scrutation des entrées est paramétrable
        dans les options du plugin. 
        """
        Debug("KinconyCheckInputs - Lancement du thread")
        self.frequence_check = int(Parameters["Mode5"])
        Debug("Fréquence de raffraichissement : " + str(int(self.frequence_check) * 50) + " ms + temps de cycle d'environ 100 ms")
        while not self.stop_thread:
            self.UpdateDomoticz(True, False)
            for i in range(0,self.frequence_check):
                time.sleep(0.05)
                if self.stop_thread:
                    break
        Debug("KinconyCheckInputs - Arrêt du thread")


    def KinconyConnexion(self):
        # Connexion avec la carte
        self.connexion_TCP = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connexion_TCP.settimeout(2)

        try:
            self.connexion_TCP.connect((self.host,self.port))
        except socket.timeout:
            Domoticz.Error("KinconyConnexion - Erreur de communication")
            self.connexion_TCP.close()
            return False
        except Exception as err:
            Domoticz.Error("KinconyConnexion - Erreur :" + str(err))
            self.connexion_TCP.close()
            return False
        Debug("KinconyConnexion - Tentative de connexion avec la carte Kincony IP:" + self.host)
        msg_recu = self.KinconyScan()
        if ("RELAY-SCAN_DEVICE-CHANNEL_" in msg_recu) and (",OK" in msg_recu):
            Debug("onStart - Esclave présent, tentative de communication")
            msg_recu = self.KinconyTest()
            if ("OK" in msg_recu):
                Domoticz.Status("KinconyConnexion - Communication OK avec la carte Kincony IP:" + self.host)
                return True
            else:
                Domoticz.Error("KinconyConnexion - Erreur de communication: '" + msg_recu + "'")
                return False
        else:
            Domoticz.Error("KinconyConnexion - Erreur de communication: '" + msg_recu + "'")
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
