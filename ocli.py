# -*- coding: utf-8 -*-
"""
OCLI - Outil d'extraction des données Optiques.

Votre travail est de construire ce module. Il correspond à la section 3
du notebook ocli_doc.ipynb.
J'ai quand même laissé quelques détails avec diverses explications
pour vous aider à démarrer.

@author: Jérôme Lacaille
"""

__date__ = "2023-02-25"
__version__ = '1.1'

import os
import re
from netCDF4 import Dataset
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display

# On importe l'objet GeoZone pour pouvoir dériver la classe Ocli
from .geozone import EARTHDIR, GeoZone

FCOVERDIR = EARTHDIR + "FCOVER/"


def getncfiles(rawdir=FCOVERDIR):
    """ GETNCFILES - Récupération sous la forme d'une table (FILE, REVISION) 
        indexée par la date des fichiers .nc.

        Quand deux fichiers ont la même date, on ne conserve que celui correspondant à la révision la plus grande.

        La table de sortie sera triée par l'index de date.
    """
    N =[]
    RT = []
    D = []
    for froot,fdir,fnames in os.walk(rawdir):
        for filename in fnames:
            if filename.endswith('.nc'):
                m = re.search('(RT[0-9])_([0-9]+)_',filename) 
                rt = int(m[1][2])
                d = pd.to_datetime (m[2],format = '%Y%m%d%H%M')
                if d in D:
                    i = D.index(d)
                    if rt>RT[i]:
                        D[i] = d
                        RT[i] = rt
                        N[i] = os.path.join(froot,filename)
                else:
                    N.append(os.path.join(froot,filename))
                    D.append(d) 
                    RT.append(rt) 
    df = pd.DataFrame({'DATE': D, 'FILE' : N, 'REVISION' : RT})
    # On met la date en index.
    df.index = df['DATE']

    # Du coup on n'a plus besoin de la colonne correspondate.
    df.drop(columns="DATE",inplace=True)

    # Finalement on trie la table.
    df.sort_index(inplace=True)
    
    return df

# -------------------------------------------------------------------------
class Ocli(GeoZone):
    """ Ocli - Un objet définissant des zones géographiques et leur
        correspondance graphique.

        Cette classe dérive de GeoZone, il faut donc faire appel au constructeur de la classe mère, c'est assez facile en Python par l'appel de la fonction super().

        On va aussi compléter la méthode système d'affichage __repr__ pour différentier de la classe de base (testez pour voir sans cette méthode).
    """
    
    def __init__(self, rawdir=FCOVERDIR, geomap="map.geojson"):
        """ Initialise la classe GeoZone, puis récupère la liste des fichiers.
        """
        super().__init__(geomap)
        
        # On stocke la liste des noms de zones.
        self.geomap = geomap
        self.names = [z['name'] for z in GeoZone(geomap)]


        # Récupération de la liste des fichiers.
        self.rawdir = rawdir
        self.df = getncfiles(rawdir)
        self.dates = [d.strftime('%d-%m-%Y') for d in self.df.index]
    
    def __repr__(self):
        """ 
        Affichage de base de l'objet Ocli.
        """
        return f"Ocli ({self.geomap}) - " + super().__repr__()
    
    def ncfilebydate(self, date):
        """ 
        Récupère le nom du fichier associé à une date.
        """
        i = None
        try :
            for d in self.dates:
                if d == date:
                    i = self.dates.index(date)
        except i == None:
            print("Il n'existe pas de fichiers à cette date")
            return None

        return self.df.FILE[i]

    def values(self,date,name):
        """ 
        Récupère le tableau des données.
        """
        lat0,lon0,lat1,lon1 = self.bboxbyname(name)
        fname = self.ncfilebydate(date)

        with Dataset(fname, 'r') as nc:
            # Cacul des coordonnées utiles.
            lon = nc.variables['lon'][:].data
            lat = nc.variables['lat'][:].data

            # Extraction des données FCOVER.
            bx = np.logical_and(lon0<=lon, lon<=lon1)
            by = np.logical_and(lat0<=lat, lat<=lat1)
            fc = nc.variables['FCOVER'][0,by,bx]

            # On gère le masque par des NaN.
            F = fc.data
            F[fc.mask] = np.nan
        
        return F

    def plot(self,date,name):
        """ 
        Affiche une zone.
        """
        plt.clf()
        F = self.values(date,name)
        plt.imshow(F)
        plt.title(name + " [FCOVER] le " + date )
        plt.show()

    def iplot(self):
        """ 
        Affichage interactif.
        """
        interactive_widget = widgets.interactive(self.plot, date=self.dates, name=self.names);
        display(interactive_widget)
