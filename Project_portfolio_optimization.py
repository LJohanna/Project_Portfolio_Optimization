# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 20:49:57 2016

@author: johannalalou
"""
#Nous étudions dans un premier temps le modèle min Variance

#Nous créons des fichiers excels contenant l'ensemble des données rendements-volatilités des sociétés du CAC 40.
#Méthodes:
#   -   rdt_annual(stock="DATAFRAME",t="INT")
#   -   vlt_annual(stock="DATAFRAME",t="INT")
#   -   create_csv(corpo="EXCEL",t="INT")

import pyensae
import pandas
import math
import numpy as np
import random
from cvxopt import matrix,solvers,spdiag,sparse

def rdt_annual(stock,t):
    #Description:
    #Fonction numérique qui calcule le rendement annuel d'une action à partir d'un trimestre donné
    # ----------------------------------------------------------------------------
    #stock - DATAFRAME - L'ensemble des cours de l'action, à partir du premier jour de l'historique des données.
    #t   -   INT     - L'année entrée par l'utilisateur, du type 0,1,2...
    # ----------------------------------------------------------------------------
    #Return:
    #rdt -   FLOAT   - Le rendement annuel de l'action sur l'année considérée.
    rdt=0
    a=t*(55) # Le point de départ  du calcul varie selon le t entré
    #Etude sur 1 an (220 jours de trading)
    for i in range(0,220):
        rdt+=(stock['Open'][a+i+1]-stock['Open'][a+i])/stock['Open'][a+i] #
    return rdt

def vlt_annual(stock,t):
    #Description:
    #Fonction numérique qui calcule la volatilité annuelle d'une action sur une année précise.
    #----------------------------------------------------------------------------
    #stock   - DATAFRAME - L'ensemble des cours de l'action, à partir du premier jour de l'historique des données.
    #t   -   INT     - L'année entrée par l'utilisateur.
    #----------------------------------------------------------------------------
    #Return:
    #vlt -   FLOAT   - La volatilité annuelle de l'action sur l'année considérée, qui correspond à l'écart type des données.
    moy=0
    vlt=0
    #Etude sur 1 an (220 jours de trading)
    for i in range (0,220):
        moy+=stock['Close'][a+i]
    moy/=220
    
    for i in range(0,220):
        vlt+=math.pow((stock['Close'][a+i]-moy),2)
    vlt/=220
    vlt=math.sqrt(vlt)

    return vlt

def create_csv(corpo,t):
    #Description:
    #Fonction numérique qui calcule les rendements-volatilité annuels de l'ensemble des actions présentes dans le CAC40 sur une certaine période t & 
    #création d'autant de fichiers CSV que de dates contenant les données.
    #----------------------------------------------------------------------------
    #Input:
    #corpo  - Excel - Fichier contenant l'ensemble des Sigles des entreprises du CAC40.
    #t   - Int - Date d'étude de l'analyse entrée par l'utilisateur.
    #----------------------------------------------------------------------------
    #Return:
    #None. (Création des fichiers CSV)
    l=[]
    for i in range(1,t):
        l.append(i)

    for i in l:
        rdt_x=[]
        vlt_x=[]
        rdt_CAC40=0

        for sigles in corpo['Sigle']:
            stock = pyensae.StockPrices(tick = sigles) # On utilise ici le tick de la série financière utilisé par le site Yahoo Finance (voir pyensae Stockprices).
            stockdf = stock.df()
            rdt_x.append(rdt_annual(stockdf,i))
            vlt_x.append(vlt_annual(stockdf,i))

        #Ajout des données au fichier au corpo
        corpo['Rendement annuel']=rdt_x
        corpo['Volatilite annuelle']=vlt_x
        temp=[]
        temp.append(sum(rdt_x)/39)
        for k in range(0,38):
            temp.append("")
        corpo['Rendement CAC40']=temp

        #Conversion & Création des fichiers Rendements-Volatilités en .CSV
        j = str(i)
        rdt = "Rendements-volatilites"+j+".csv"
        corpo.to_csv(rdt,index=False,encoding='utf-8',float_format='%.3f')
        
# Dans cette partie, nous constituons le portefeuille d'actions associé des couples rendements-volatilités pour l'ensemble des périodes étudiées

def select_asset():
    #Description:
    #Fonction permettant la selection des actions constituant le portefeuille
    #-----------------------------------------------------------------------
    #Return:
    #stocks - LIST - l'ensemble des sigles correspondant aux actions selectionnées par l'utilisateur
    #R0  - FLOAT - le rendement espéré du portefeuille.
    stocks_asset = []
    df=pandas.read_csv("Rendements-volatilites.csv")
    print(df)
    stocks_asset=input("Donner le sigle des actions du portefeuille:  ")
    print("Les actions du portefeuille sont : \n",stocks_asset,"\n")
    #Choix du rendement
    R0=float(input("Rendement voulu"))
    return stocks_asset, R0

#Creation de la liste de rendements et de volatilié associées
def rdtvlt_portfolio(stocks_asset,d):
    #Description:
    #Fonction qui lit les fichiers créés par le module rdt_vlt_CAC40 & selectionne les rendements-volatilités correspondant aux actions 
    #entrées en amont par l'utilisateur.
    #-----------------------------------------------------------------------
    #stocks_asset - LIST - Les actions selectionnées par l'utilisateur
    #d - INT - Le nombre d'années correspondant à la durée de l'analyse 
    #-----------------------------------------------------------------------
    #Return:
    #rdt - DICTIONNAIRE - les rendements correspondant aux actions du portefeuille sur l'ensemble des années.
    #vlt - DICTIONNAIRE - les volatilités correspondants aux actions du portefeuille sur l'ensemble des années. 
    rdt = dict()
    vlt = dict()
    for i in range(d+1):
        #Lecture des rendements-volatilités correspondant à chaque année 
        corpo="Rendements-volatilites"+str(i)+".csv"
        df=pandas.read_csv(corpo)

        #Ajout des données dans les listes associées
        rdt_d=[]
        vlt_d=[]
        sigles=list(df["Sigle"])
        for z in stocks_asset:
            if z in sigles:
                n=sigles.index(z) 
                rdt_d.append(df["Rendement annuel"][n])
                vlt_d.append(df["Volatilite annuelle"][n])        
        rdt[i] = rdt_d
        vlt[i] = vlt_d

        
    return rdt, vlt



def listeegale(a,n): 
    #Description : 
    #Fonction qui génère une liste de taille n avec l'élément a
    #-----------------------------------------------------------------------
    #a - - Element à mettre dans la liste
    #n - INT - Taille de la liste en sortie
    #----------------------------------------------------------------------
    #res - LIST - Liste de taille n remplie d'éléments a
    res=[]
    for i in range(0,n):
        res.append(a)
    return res

#Mise en place de l'optimisation via cvxopt

#On veut minimiser la volatilité sous la contrainte de rendement ( le rendement est choisi en amont )
# Problème : min 1/2(<X,V>)
#     s.c  AX = b     i.e x+y+z=1 (contrainte de budget dans le cas de 3 actions par exemple)
#     s.c  GX <= h    i.e x*Rx+yRy+zRz >= R0 et x>=0  y>=0 z>=0  car nous considérons l'achat seulement

def optimisation(stocks_asset,rdt,vlt,R0):
    #Description : 
    #Fonction qui optimise le portefeuille, i.e. trouve les poids de chaque action pour minimiser la volatilité sous contrainte de rendement
    #Les poids trouvés ici sont positifs : achat seulement
    #-----------------------------------------------------------------------
    #stocks_asset - LIST - Liste avec le nom des actions du portefeuille
    #rdt - DICTIONNAIRE - Les rendements correspondant aux actions du portefeuille sur l'ensemble des années.
    #vlt - DICTIONNAIRE - Les volatilités correspondant aux actions du portefeuille sur l'ensemble des années.
    #R0 - FLOAT - Rendement voulu
    #-----------------------------------------------------------------------
    #Return:
    #poids_finaux - LIST - Liste des poids obtenus
    #rdtfinal - FLOAT - Rendement obtenu
    #volfinal - FLOAT - Volatilité obtenue
    
    rendements=rdt[0] 
    volatilites=vlt[0]
    rendementsc=[]
    for i in rendements:
        rendementsc.append((-1.0)*i)
   
    n=len(rendements)
    #Fonction pour cvxopt
    def fonction(x=None,z=None) :
        if x is None :
            x0 = matrix ( [[ random.random() for i in range(0,n) ]]) # il faut choisir un x initial, c'est ce qu'on fait ici. L’algorithme de résolution est itératif : on part d’une point x0 qu’on déplace dans les directions opposés aux gradients de la fonction à minimiser et des contraintes jusqu’à ce que le point xt n’évolue plus. 
            return 0,x0

        f = 0
        for i,j in enumerate(volatilites):
            f=f+j*x[i]
        f=(1/2)*(f**2)
        tempd=[]
        for i in volatilites:
            tempd.append(i*np.vdot(x,volatilites)) 
           
        d = matrix ( tempd ).T     #gradient de la fonction f
        temph=[]
        for i in volatilites:
            temp2=listeegale(i,n)
            temph.append([p*q for p,q in zip(temp2,volatilites)])
        h=matrix(temph)             #hessienne de la fonction f
        if z is None: return  f, d
        else : return f, d, h
    ones=[]
    for i in range(0,n):
        ones.append(1.0)
    
    #Matrice des contraintes d'égalité
    A = matrix([ ones ]).trans()
    b = matrix ( [[ 1.0]] )

    #Création de la matrice de contraintes d'inégalités
    pp = matrix ( [rendementsc]).trans()
    In=spdiag(ones)
    G=sparse([pp,-In]) #On concatène les rendements et - Identité
    z=[]
    z.append(-R0)
    for i in range(0,n):
        z.append(0)
    h = matrix ( [z] )
    sol = solvers.cp ( fonction, A = A, b = b, G=G, h=h)
    

    #Solution
    vol,dvol=fonction(sol['x'])
    volfinal=(2*vol)**(0.5)
    rdtfinal=np.vdot(sol['x'],rendements)
    poids_finaux=sol['x'].T
    
    #Affichage des résultats finaux 

    print('\n****************************\n')
    print("Volatilite atteinte : ",volfinal)
    print("Rendement voulu : ",R0)
    print("Rendement atteint : ",rdtfinal)
    print('\n****************************\n')
    print("Les actions du portefeuille sont : ",stocks_asset)
    print ("Solution : ",poids_finaux)
    return poids_finaux,rdtfinal,volfinal
    
    

def backtest(coeff,rdt,vlt,t):

    #Description:
    #Fonction faisant le backtest de notre stratégie d'investissement. Elle étudie le rendement et la volatilité atteinte avec nos poids obtenus sur des périodes antérieures.
    #-----------------------------------------------------------------------
    #Input:
    #coeff - LIST - Poids des actions dans le portefeuille obtenus grace à l'optimisation
    #rdt - DICTIONNAIRE - les rendements correspondant aux actions du portefeuille sur l'ensemble des années.
    #vlt - DICTIONNAIRE - les volatilités correspondants aux actions du portefeuille sur l'ensemble des années.
    #t - INT - Nombre de périodes d'étude (déjà défini auparavant)
    #-----------------------------------------------------------------------
    #Return:
    #Génère des graphiques présentant l'évolution du rendement et de la volatilité au cours du temps 
    #rdtmoy - FLOAT - Rendement moyen du portefeuille optimisé sur la période étudiée
    #vltmoy - FLOAT - Volatilité moyenne du portefeuille optimisée sur la période étudiée
    #rendements - LIST - Liste des rendements sur les périodes étudiées
    temps=[]
    rCAC40=[]
    vsansrisque=[]
    for i in range(0,t+1):
        temps.append(i)
        corpo="Rendements-volatilites"+str(i)+".csv"
        df=pandas.read_csv(corpo)
        rCAC40.append(df['Rendement CAC40'][i])     # On cherche à tracer l'évolution du rendement du CAC40 et la comparer avec celui de notre portefeuille
    rendements=[]
    volatilites=[]
    for i in range(0,t+1):
        a=0
        b=0
        for j in range(0,len(rdt[i])):
            a+=coeff[j]*rdt[i][j]
            b+=coeff[j]*vlt[i][j]
        rendements.append(a)
        volatilites.append(b)
    
    plt.plot(temps,rendements)
    plt.plot(temps,rCAC40,'--r',label='Rendement CAC40')
    plt.xlabel('Temps')
    plt.ylabel('Rendement du portefeuille')
    plt.legend()
    plt.title('Evolution du rendement au cours du temps')
    plt.savefig('images/Evolution du rendement.png')
    
    
    vltmoy=0
    rdtmoy=0
    for i in range(0,len(rendements)):
        vltmoy+=volatilites[i]
        rdtmoy+=rendements[i]
    rdtmoy=rdtmoy/t
    vltmoy=vltmoy/t
    return rdtmoy, vltmoy,rendements


#Au final:

#Lecture de la liste des entreprises du CAC40
entreprises=pandas.read_excel('entreprises.xlsx')

#Création des fichiers sur les années 
t=input("Nombre de trimestres d'étude : ")
t=int(t)
create_csv(entreprises,t)

#Choix des actions dans le portefeuille
stock,R0=select_asset()

#Création des dictionnaires de rendements/volatilités au cours du temps
rdt,vlt=rdtvlt_portfolio(stock,t)

#Optimisation du portefeuille (minimisation de la volatilité sous contrainte de rendement)
coeff,rdtfinal,vltfinal=optimisation(stock,rdt,vlt,R0)

#Evolution du portefeuille sur les années antérieures (backtest)
rdtmoy,vltmoy,rendements=backtest(coeff,rdt,vlt,t)

#Dans un deuxième temps, nous étudions le modèle Equal Risk contribution: chaque action doit contribuer de manière équitable au risque du portefeuille
#Je voulais mener le modèle à son terme et je n'ai pas trouvé de moyens pour calculer les poids en enlevant l'indépendance de l'évolution des cours des actions, ce qui est bien évidemment faux mais me permet d'avancer.

def coeffERC(stocks_asset,Vol,t,rdt,vlt):
    #Description:
    #Cette fonction cherche les poids associés à chaque action afin qu'elle participe de la même façon que les autres au risque du portefeuille
    #-----------------------------------------------------------------------
    #stocks_asset - LIST - Les actions selectionnées par l'utilisateur
    #rdt - DICTIONNAIRE - les rendements correspondant aux actions du portefeuille sur l'ensemble des années.
    #vlt - DICTIONNAIRE - les volatilités correspondants aux actions du portefeuille sur l'ensemble des années.
    #Vol: volatilité du portefeuille
    #t   - Int - Date d'étude de l'analyse entrée par l'utilisateur.
    #-----------------------------------------------------------------------
    #Return:
    #coeff - LIST - Poids des actions dans le portefeuille obtenus grâce à la méthode
    #rendements - LIST - Liste des rendements sur les périodes étudiées
    coeff=[]
    Voldiv=Vol/len(stocks_asset)
    for i in range(t+1):
        corpo="Rendements-volatilites"+str(i)+".csv"
        df=pandas.read_csv(corpo)
        for z in stocks_asset:
                n=stocks_asset.index(z) 
                coeff.append(Voldiv/df["Volatilite annuelle"][n])
    rendements=[]
    for i in range(0,t+1):
        a=0
        for j in range(0,len(rdt[i])):
            a+=coeff[j]*rdt[i][j]
        rendements.append(a)
    return coeff,rendements     
             
                
    coeff,rendements1=coeffERC(stocks_asset,vltfinal,t,rdt,vlt)
    plt.plot(temps,rendements1)
    plt.xlabel('Temps')
    plt.ylabel('Rendement du portefeuille')
    plt.legend()
    plt.title('Evolution du rendement au cours du temps')
  
    # On compare les rendements du portefeuille avec le modèle ERC et le modèle Min-Variance pour déterminer 
    #les périodes où on utilise un modèle ou l'autre, suivant le rendement qu'apporte le portefeuille. 
    #Nous pouvons même pondérer les poids des deux modèles pour chaque action afin de déterminer un nouveau poids pour chaque action.
        
        
    
    
    


