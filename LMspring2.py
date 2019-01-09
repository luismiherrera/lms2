#########################################################################
#                                                                       #
#                            LMspring 2                                 #
#                        by Luismi Herrera.                             #
#                     Twitter: @luismiherrera                           #
#                                                                       #
#########################################################################

import maya.cmds as cmds
import maya.mel
import random
import os
from urllib2 import urlopen, URLError, HTTPError
import shutil
import tempfile

class LMspring(object):
    def __init__(self):
        self.installedVersion = '2.01'
        self.minTime = cmds.playbackOptions(minTime=True, query=True)
        self.maxTime = cmds.playbackOptions(maxTime=True, query=True)
        self.sel = cmds.ls(selection=True)
        self.units = cmds.currentUnit(query=True, linear=True)
        self.modifier = 1.0
        self.windowWidth = 250
        self.windowHeight = 250
        self.selChain = []
        self.i = 100
        self.originalWeight = 0.45
        self.axis = [0,0,0]
        #optionVar variables
        self.bakeVar = True
        self.bakeOption = self.bakeVar
        if(cmds.optionVar(exists='LMspringBakeVar')):
            self.bakeVar = cmds.optionVar(query='LMspringBakeVar')
        self.locSizeSmall = True
        if(cmds.optionVar(exists='LMspringlocSizeSmallVar')):
            self.locSizeSmall = cmds.optionVar(query='LMspringlocSizeSmallVar')
        self.locSizeMedium = False
        if(cmds.optionVar(exists='LMspringlocSizeMediumVar')):
            self.locSizeMedium = cmds.optionVar(query='LMspringlocSizeMediumVar')
        self.locSizeBig = False
        if(cmds.optionVar(exists='LMspringlocSizeBigVar')):
            self.locSizeBig = cmds.optionVar(query='LMspringlocSizeBigVar')
        #toltip text
        self.sbmLocator = 'Creates locator to aim to.'
        self.sbmPrevis = 'Previs simulation.'
        self.sbmWeightSlider = 'Overlapping amount.'
        self.sbmDecaySlider =  'Decay amount.'
        self.sbmBake = 'Bake previs to selection.'
        self.sbmClear = 'Deletes LMspring nodes.'
        self.sbmSendToShelf = 'Creates a Shelf button with latest selection and settings.'
        self.sbmAddSelection = 'Add current selected objects to the field.'

    def updateOptionVars(self):
        locSizeSmall = cmds.radioButton(self.locSmall, query=True, select=True)
        cmds.optionVar(iv=('LMspringlocSizeSmallVar', int(locSizeSmall)))
        locSizeMedium = cmds.radioButton(self.locMedium, query=True, select=True)
        cmds.optionVar(iv=('LMspringlocSizeMediumVar', int(locSizeMedium)))
        locSizeBig = cmds.radioButton(self.locBig, query=True, select=True)
        cmds.optionVar(iv=('LMspringlocSizeBigVar', int(locSizeBig)))

    def getTimeSlider(self):
        self.minTime = cmds.playbackOptions(minTime=True, query=True)
        self.maxTime = cmds.playbackOptions(maxTime=True, query=True)

    #returns 1,2,3,-1,-2,-3
    def getDirection(self):
        self.axis = []
        self.axis.append(cmds.getAttr(self.aimLoc[0] + '.translateX'))
        self.axis.append(cmds.getAttr(self.aimLoc[0] + '.translateY'))
        self.axis.append(cmds.getAttr(self.aimLoc[0] + '.translateZ'))

        direction = self.axis.index(max(self.axis, key=abs)) + 1
        if(self.axis[direction-1]<0):
            direction = direction * -1
        return direction

    def preCreateLocator(self, *args):
        self.updateOptionVars()
        self.sel = cmds.ls(selection=True)
        if(len(self.sel)>1):
            self.selChain = self.sel
            self.i = 0
        if(cmds.radioButton(self.rbRot,query=True, select=True)):
            if len(self.sel) == 0:
                cmds.warning( "Nothing selected." )
            else:
                if(cmds.objExists('LMspringAimLoc')):
                    cmds.warning('There is a LMspring Locator in the scene! Use Previs or Clear the scene.')
                else:
                    self.createLocator()
        else: #This is redundant now because the button is deactivated in Translation mode
            cmds.warning('You only need to create a Locator in Rotation mode.')
        cmds.setFocus("MayaWindow")

    def createLocator(self, *args):
        aimLocGrp = cmds.group(name='LMspringAimLocGrp', empty=True)
        cmds.parentConstraint(self.sel[0], aimLocGrp, mo=False)
        self.aimLoc = cmds.spaceLocator(name='LMspringAimLoc')
        cmds.parent(self.aimLoc,aimLocGrp,relative=True)
        self.resizeLocator(self.aimLoc)

    def resizeLocator(self,locator):
        locSize = 1
        if(cmds.radioButton(self.locSmall, query=True, select=True)):
            locSize = 0.1
        if(cmds.radioButton(self.locMedium, query=True, select=True)):
            locSize = 1
        if(cmds.radioButton(self.locBig, query=True, select=True)):
            locSize = 10
        cmds.setAttr(locator[0] + 'Shape.localScaleX', (1/self.modifier)*locSize)
        cmds.setAttr(locator[0] + 'Shape.localScaleY', (1/self.modifier)*locSize)
        cmds.setAttr(locator[0] + 'Shape.localScaleZ', (1/self.modifier)*locSize)
        cmds.setFocus("MayaWindow")

    def springPrevis(self, *args):
        self.getTimeSlider()
        #previs translation
        if(cmds.radioButton(self.rbTras,query=True, select=True)):
            self.sel = cmds.ls(selection=True)
            print('previsTrans')
            if len(self.sel) == 0:
                cmds.warning( "Nothing selected." )
            else:
                if(cmds.objExists('LMspring')):
                    cmds.warning('There are existing LMspring particles in the scene! Use Spring Bake or delete the LMspring group.')
                else:
                    cmds.group(name='LMspring', empty=True)
                    for i in range(len(self.sel)):
                        cmds.currentTime( self.minTime, edit=True )
                        selLoc = cmds.spaceLocator(name='OriginalPosition_Loc'+str(i))
                        self.resizeLocator(selLoc)
                        luismiPart =cmds.particle(p=[(0, 0, 0)], name='luismiParticle'+str(i))
                        tempConst = cmds.parentConstraint(self.sel[i],selLoc,mo=False)
                        cmds.bakeResults(selLoc, t=(self.minTime,self.maxTime))
                        cmds.delete(tempConst)
                        tempConst2 = cmds.parentConstraint(selLoc,'luismiParticle'+str(i),mo=False)
                        cmds.delete(tempConst2)
                        cmds.goal( 'luismiParticle'+str(i), g=selLoc, w=.55)
                        phyLoc = cmds.spaceLocator(name='physicsLoc'+str(i))
                        self.resizeLocator(phyLoc)
                        expression = 'physicsLoc{0}.translateX = luismiParticle{0}Shape.worldCentroidX/{1};physicsLoc{0}.translateY = luismiParticle{0}Shape.worldCentroidY/{1};physicsLoc{0}.translateZ = luismiParticle{0}Shape.worldCentroidZ/{1};'.format(i, self.modifier)
                        cmds.expression(object='physicsLoc'+str(i),string=expression)
                        tempConst3 = cmds.pointConstraint('physicsLoc'+str(i), self.sel[i], mo=True)
                        cmds.parent(selLoc, luismiPart, phyLoc, 'LMspring')
                    cmds.select(self.sel)

        #previs rotation
        if(cmds.radioButton(self.rbRot,query=True, select=True)):
            if((cmds.objExists('LMspringAimLoc') or cmds.objExists('*:LMspringAimLoc')) and cmds.objExists('LMspring')==False):
                direction = self.getDirection()
                cmds.group(name='LMspring', empty=True)
                cmds.currentTime( self.minTime, edit=True )
                selLoc = cmds.spaceLocator(name='OriginalPosition_Loc')
                self.resizeLocator(selLoc)
                luismiPart =cmds.particle(p=[(0, 0, 0)], name='luismiParticle')
                tempConst = cmds.parentConstraint(self.aimLoc[0],selLoc,mo=False)
                cmds.bakeResults(selLoc, t=(self.minTime,self.maxTime))
                cmds.delete(tempConst)
                tempConst2 = cmds.parentConstraint(selLoc,'luismiParticle',mo=False)
                cmds.delete(tempConst2)
                cmds.goal( 'luismiParticle', g=selLoc, w=.55)
                phyLoc = cmds.spaceLocator(name='physicsLoc')
                self.resizeLocator(phyLoc)
                tempConst3 = cmds.parentConstraint(selLoc,phyLoc,mo=False)
                cmds.delete(tempConst3)
                expression = 'physicsLoc.translateX = luismiParticleShape.worldCentroidX/{0};physicsLoc.translateY = luismiParticleShape.worldCentroidY/{0};physicsLoc.translateZ = luismiParticleShape.worldCentroidZ/{0};'.format(self.modifier)
                cmds.expression(object='physicsLoc',string=expression)
                tempConst3 = cmds.pointConstraint('physicsLoc', self.aimLoc[0], mo=True)
                cmds.parent(selLoc, luismiPart, phyLoc, 'LMspring')
                if (direction == 1):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(1,0,0), upVector=(0,0,1), worldUpVector=(0,0,1), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
                if (direction == 2):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(0,1,0), upVector=(0,0,1), worldUpVector=(0,0,1), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
                if (direction == 3):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(0,0,1), upVector=(1,0,0), worldUpVector=(1,0,0), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
                if (direction == -1):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(-1,0,0), upVector=(0,0,1), worldUpVector=(0,0,1), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
                if (direction == -2):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(0,-1,0), upVector=(0,0,1), worldUpVector=(0,0,1), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
                if (direction == -3):
                    tempAimConst = cmds.aimConstraint(phyLoc[0], self.sel[0], aimVector=(0,0,-1), upVector=(1,0,0), worldUpVector=(1,0,0), worldUpObject=(selLoc[0]), worldUpType='objectrotation', mo=False)
            else:
                cmds.warning('Create a Locator to aim to first or Clear the scene.')

        self.updateWeight()
        cmds.setFocus("MayaWindow")

    def updateWeight(self, *args):
        particle = cmds.ls('luismiParticle*')
        for i in range (len(particle)):
            cmds.setAttr(particle[i]+'.goalWeight[0]', (1.0 - cmds.floatSliderGrp(self.weightSlider, value=True, query=True)))

        cmds.setFocus("MayaWindow")

    def updateDecay(self, *args):
        #print()
        cmds.setFocus("MayaWindow")


    def springBakeFromMenu(self, *args):
        cmds.optionVar(iv=('LMspringBakeVar', int(cmds.checkBox(self.bakeOption, query=True, value=True))))
        self.springBake(cmds.checkBox(self.bakeOption, query=True, value=True), cmds.floatSliderGrp(self.decaySlider, query=True, value=True))
        cmds.setFocus("MayaWindow")

    def springBake(self, bakeToLayer, decay):
        self.getTimeSlider()
        if(cmds.objExists('luismiParticle*')):
            # print('weight: '+str(cmds.floatSliderGrp(self.weightSlider, value=True, query=True)))
            # print('decay: '+str(decay))
            # print('goalWeight[0]: '+str(1.0 - (cmds.floatSliderGrp(self.weightSlider, value=True, query=True)/decay)))
            cmds.bakeResults(self.sel, t=(self.minTime,self.maxTime), bol=bakeToLayer, preserveOutsideKeys = True, simulation=True)
            self.clear()
            self.deleteBlendAimAttr(self.sel[0])
            self.deleteBlendPointAttr(self.sel[0])
        else:
            cmds.warning( "Nothing to bake." )

        self.i=self.i+1
        while self.i < len(self.selChain):
            #print('self.i = ' + str(self.i))
            #print('len(self.selChain) = '+str(len(self.selChain)))
            if(self.i == 1):
                self.originalWeight = cmds.floatSliderGrp(self.weightSlider, value=True, query=True)
                print('Original Weight: '+str(self.originalWeight))
            cmds.select(self.selChain[self.i])
            self.sel=cmds.ls(selection=True)
            self.createLocator()
            self.moveLocator()
            self.setWeight(cmds.floatSliderGrp(self.weightSlider, value=True, query=True), decay)
            self.springPrevis()
            self.springBake(bakeToLayer, decay)
        if(self.i == (len(self.selChain))):
            #print('Updating weight to original weight!')
            cmds.floatSliderGrp(self.weightSlider, edit=True, value=self.originalWeight)

    def moveLocator(self):
        cmds.setAttr(self.aimLoc[0] + '.translateX', self.axis[0])
        cmds.setAttr(self.aimLoc[0] + '.translateY', self.axis[1])
        cmds.setAttr(self.aimLoc[0] + '.translateZ', self.axis[2])

    def moveLocatorTo(self, xPos, yPos, zPos):
        cmds.setAttr(self.aimLoc[0] + '.translateX', xPos)
        cmds.setAttr(self.aimLoc[0] + '.translateY', yPos)
        cmds.setAttr(self.aimLoc[0] + '.translateZ', zPos)

    def setWeight(self, weight, decay):
        weight = weight/decay
        cmds.floatSliderGrp(self.weightSlider, edit=True, value=weight)

    def deleteBlendPointAttr(self, ctrl):
        if(cmds.attributeQuery('blendPoint1', node=ctrl, exists=True)):
            cmds.deleteAttr(ctrl+'.blendPoint1')

    def deleteBlendAimAttr(self, ctrl):
        if(cmds.attributeQuery('blendAim1', node=ctrl, exists=True)):
            cmds.deleteAttr(ctrl+'.blendAim1')

    def clear(self, *args):
        LMspringObjects = cmds.ls('LMspring*', '*:LMspring*')
        if(len(LMspringObjects)>0):
            cmds.delete(LMspringObjects)
        else:
            cmds.warning('Nothing to clear.')
        cmds.setFocus("MayaWindow")

    def toogleLocatorButton(self, *args):
        btnEnabled = cmds.button(self.locBtn, query=True, enable=True)
        if(btnEnabled):
            cmds.button(self.locBtn, edit=True, enable=False)
        elif(not btnEnabled):
            cmds.button(self.locBtn, edit=True, enable=True)
        self.clear()

    def shelfButton(self, *args):
        if(cmds.textField(self.selectionFld, query=True, text = True)!=''):
            gShelfTopLevel = maya.mel.eval('$tmpVar=$gShelfTopLevel')
            dirName = os.path.dirname(__file__)
            iconImage = dirName + '\LMspring2PresetIcon.png'
            labelText= cmds.textField(self.shelfButtonLabelFld, query=True, text=True)
            sbmShelfButton = cmds.textField(self.shelfButtonTooltipFld, query=True, text=True)

            lmspringPreset = (
                            "import maya.cmds as cmds\n"
                            "import LMspring2.LMspring2 as lms2\n" #Generic. should be romoved or changed depending on the folder where the script lives
                            "try:\n"
                            "\tcmds.select({0}, r=True)\n"
                            "\tlmspring = lms2.LMspring()\n"
                            "\tlmspring.executeShelfButton({1},{2},{3},{4},{5},{6})\n"
                            "except:\n"
                            "\tcmds.warning('LMspring2 cannot find the object/s in the current scene.')"
                            ).format(
                                    cmds.textField(self.selectionFld, query=True, text = True),
                                    cmds.textFieldGrp(self.locatorOffsetXFld, query=True, text = True),
                                    cmds.textFieldGrp(self.locatorOffsetYFld, query=True, text = True),
                                    cmds.textFieldGrp(self.locatorOffsetZFld, query=True, text = True),
                                    cmds.floatSliderGrp(self.weightPresetSliderFld, query=True, value=True),
                                    cmds.floatSliderGrp(self.decayPresetSliderFld, query=True, value=True),
                                    cmds.checkBox(self.bakeOptionPreset, query=True, value=True)
                                    )
            currentShelf = cmds.tabLayout(gShelfTopLevel, query=True, selectTab=True)
            cmds.setParent(currentShelf)
            cmds.shelfButton( annotation='Print "Hello".', image1=iconImage, imageOverlayLabel=labelText,overlayLabelColor=(0.0,1.0,1.0),overlayLabelBackColor=(0,0,0,0),
                            statusBarMessage=sbmShelfButton, command=lmspringPreset )
            cmds.setFocus("MayaWindow")

    def executeShelfButton(self,locX,locY,locZ,weight,decay,bake):
        self.showUI()
        self.preCreateLocator()
        self.moveLocatorTo(locX,locY,locZ)
        cmds.floatSliderGrp(self.weightSlider, edit=True, value=weight)
        self.springPrevis()
        self.springBake(bake,decay)
        self.closeUI()

    def addSelection(self, *args):
        print('adding selection!')
        currentSel = cmds.ls(selection=True)
        if(len(currentSel)>0):
            self.selText=("'"+currentSel[0]+"'")
            for i in range(1, len(currentSel)):
                self.selText = (self.selText + ", '" + str(currentSel[i])+"'")
            cmds.textField(self.selectionFld, edit=True, text = self.selText)
        else:
            cmds.warning('Nothing selected!')

    def checkForUpdatesAtStart(self):
        version_url = 'https://raw.githubusercontent.com/luismiherrera/lms2/master/version'

        self.latestVersion = self.installedVersion
        try:
            fversion = urlopen(version_url)
            for self.latestVersion in fversion:
                print ('Installed Version: ' + self.installedVersion)
                print ('Latest Version: ' + self.latestVersion)

        except HTTPError, e:
            print ("HTTP Error:", e.code)
        except URLError, e:
            print ("URL Error:", e.reason)

        if(self.latestVersion[:4] != self.installedVersion[:4]):
            result = cmds.confirmDialog(title='Updater',
                                message='LMspring {0} is available'.format(self.latestVersion),
                                button=['Install','Cancel'], defaultButton='Install', cancelButton='Cancel', dismissString='Cancel',
                                messageAlign='right',
                                icon='warning',
                                parent='LMspringWindow',
                                bgc=(0.2,0,0))
            if(result=='Install'):
                self.updateLMspring2()

    def checkForUpdates(self, *args):
        self.checkForUpdatesAtStart()
        if(self.latestVersion[:4] == self.installedVersion[:4]):
            cmds.confirmDialog(title='Updater', message='You have the latest version of LMspring 2.',parent='LMspringWindow')

    def updateLMspring2(self):
        print('Updating LMspring2!')
        urlNewVersion = 'https://github.com/luismiherrera/lms2/raw/master/LMspring2.pyc'
        userLMspringDir = cmds.internalVar(userScriptDir=True)+('LMspring2/')
        newVersionFileLocation = userLMspringDir+'LMspring2.pyc'
        try:
            fpy = urlopen(urlNewVersion)
            with open(newVersionFileLocation,'wb') as f:
                f.write(fpy.read())
                f.close()
            result = cmds.confirmDialog(title='Updater', message='LMspring has been updated!. Please, RELOAD LMspring 2.', icon='warning',parent='LMspringWindow')
            if (result=='Confirm'):
                self.closeUI()
        except HTTPError, e:
            print ("HTTP Error:", e.code)
            cmds.confirmDialog(title='Updater', message='There was an error trying to get the latest version.', icon='critical',parent='LMspringWindow')
        except URLError, e:
            print ("URL Error:", e.reason)
            cmds.confirmDialog(title='Updater', message='There was an error trying to get the latest version.', icon='critical',parent='LMspringWindow')

        print('LMspring 2 Updated')


    def twitterLink(self, *args):
        cmds.showHelp( 'https://twitter.com/luismiherrera', absolute=True )

    def gumroadLink(self, *args):
        cmds.showHelp( 'https://gumroad.com/luismiherrera', absolute=True )

    def videoTutorialLink(self, *args):
        cmds.showHelp( 'https://vimeo.com/264288156', absolute=True )

    def aboutDialog(self, *args):
        cmds.confirmDialog(title='About', message='    LMspring {0}\n\n by Luismi Herrera'.format(self.installedVersion),
                            icon='information',parent='LMspringWindow',bgc=(0.2,0,0.2))

    def closeUI(self):
        cmds.deleteUI('LMspringWindow' , window=True)

    def showPresetUI(self, *args):
        if(len(self.selChain)>0):
            #selText is the string of the selection
            self.selText=("'"+self.selChain[0]+"'")
            for i in range(1, len(self.selChain)):
                self.selText = (self.selText + ", '" + str(self.selChain[i])+"'")
        else:
            self.selText = ''

        if(cmds.window('LMspringPresetWindow', exists=True)):
            cmds.deleteUI('LMspringPresetWindow')

        LMspringPresetWindow = cmds.window('LMspringPresetWindow', title='LMspring 2 Shelf Preset', widthHeight=(200, 200), mxb=False,mnb=False,sizeable=True)

        cmds.columnLayout( adjustableColumn=True)
        cmds.separator( width=100, height=20, style='in')
        cmds.radioButtonGrp( 'LMspringMode', label='Mode: ', labelArray2=['Translation', 'Rotation'], numberOfRadioButtons=2, select = 2)
        cmds.rowColumnLayout( numberOfColumns=3, columnAttach=(1, 'right', 1), columnWidth=[(1, 140), (2, 218), (3,25)] )
        cmds.text(label = 'Selection: ')
        self.selectionFld = cmds.textField()
        cmds.textField(self.selectionFld, edit=True, text = self.selText)#, changeCommand = updateLeftControlsSuffix)
        cmds.button(label='<', command=self.addSelection, sbm=self.sbmAddSelection)
        cmds.setParent('..')
        cmds.columnLayout( adjustableColumn=True )
        self.weightPresetSliderFld = cmds.floatSliderGrp( 'weightPresetSlider', label='Weight: ', field=True, precision=3, minValue=0.0, maxValue=0.9, fieldMinValue=0, fieldMaxValue=0.9, value=cmds.floatSliderGrp(self.weightSlider, value=True, query=True))
        self.decayPresetSliderFld = cmds.floatSliderGrp( 'decayPresetSlider', label='Decay: ', field=True, precision=3, minValue=1.0, maxValue=1.9, fieldMinValue=1, fieldMaxValue=1.9, value=1.2)
        self.locatorOffsetXFld = cmds.textFieldGrp(label='Locator Offset X: ', text= round(self.axis[0],3), editable=True)
        self.locatorOffsetYFld = cmds.textFieldGrp(label='Locator Offset Y: ', text= round(self.axis[1],3), editable=True)
        self.locatorOffsetZFld = cmds.textFieldGrp(label='Locator Offset Z: ', text= round(self.axis[2],3), editable=True)
        cmds.setParent('..')
        cmds.rowColumnLayout( numberOfColumns=2, columnAttach=(1, 'right', 0), columnWidth=[(1, 140), (2,243)] )

        cmds.text(label = 'Shelf Button Label: ')
        self.shelfButtonLabelFld= cmds.textField(width=100)
        cmds.textField(self.shelfButtonLabelFld, edit=True, text = 'LABEL')#, changeCommand = updateRightControlsSuffix )
        cmds.text(label = 'Shelf Button Tooltip: ')
        self.shelfButtonTooltipFld= cmds.textField()
        cmds.textField(self.shelfButtonTooltipFld, edit=True, text = 'Shelf Button Tooltip Text')#, changeCommand = updateRightControlsSuffix )
        cmds.text(label="Bake to Anim Layer: ")
        self.bakeOptionPreset = cmds.checkBox(label='', height=20, value=self.bakeVar)
        cmds.setParent('..')
        cmds.columnLayout( adjustableColumn=True )
        cmds.separator( width=100, height=20, style='in')
        cmds.setParent('..')
        cmds.rowColumnLayout(nc=5, cw=[(1,95), (2, 100), (3, 20), (4,100), (5, 20) ])
        cmds.text( label='       ' )
        cmds.button( label='Create' , width= 20, command = self.shelfButton )
        cmds.text( label='       ' )
        cmds.button( label='Close', width=20 , command=('cmds.deleteUI(\"' + LMspringPresetWindow + '\", window=True)') )
        cmds.text( label='       ' )
        cmds.text( label='       ' )
        cmds.showWindow(LMspringPresetWindow)

    def showUI(self):
        if(cmds.window('LMspringWindow', exists=True)):
            cmds.deleteUI('LMspringWindow')

        LMspringWindow = cmds.window('LMspringWindow', title='LMspring {0}'.format(self.installedVersion), widthHeight=(self.windowWidth,self.windowHeight), mxb=False,mnb=False,sizeable=True)
        cmds.columnLayout(columnAttach=('both', 2),rowSpacing=5, columnWidth=self.windowWidth)
        cmds.rowLayout(numberOfColumns=4)
        cmds.text(label='       MODE :    ')
        collection1 = cmds.radioCollection()
        self.rbTras = cmds.radioButton( label='Translation', height= 30,onCommand=self.toogleLocatorButton)
        self.rbRot = cmds.radioButton( label='Rotation', select=True, onCommand=self.toogleLocatorButton)
        cmds.setParent('..')
        cmds.columnLayout(columnAttach=('both',25),rowSpacing=5, columnWidth=self.windowWidth-5)
        self.locBtn = cmds.button( label='LOCATOR',width = 30, height=30, bgc=(0.224,.8,0.224), command=self.preCreateLocator, sbm=self.sbmLocator )
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=4)
        cmds.text(label='       SIZE: ')
        cmds.radioCollection()
        self.locSmall = cmds.radioButton( label='Small ', select=self.locSizeSmall, changeCommand='cmds.setFocus("MayaWindow")')
        self.locMedium = cmds.radioButton( label='Medium ', select=self.locSizeMedium, changeCommand='cmds.setFocus("MayaWindow")')
        self.locBig = cmds.radioButton( label='Large', select=self.locSizeBig, changeCommand='cmds.setFocus("MayaWindow")')
        cmds.setParent('..')
        cmds.columnLayout(columnAttach=('both',25),rowSpacing=5, columnWidth=self.windowWidth-5)
        cmds.button( label='PREVIS',width=119 , height=30, bgc=(0.75,.75,0.0), command=self.springPrevis, sbm=self.sbmPrevis )
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnAttach=(1, 'right', 0), columnWidth=[(1, 55), (2, 300)])
        cmds.text('  Overlap: ')
        self.weightSlider = cmds.floatSliderGrp('weightSlider', field=True, precision=3, fmn=0, fmx=0.9, min= 0, max=0.9, value=0.45, height=30, width=180, dragCommand=self.updateWeight, sbm=self.sbmWeightSlider)
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnAttach=(1, 'right', 0), columnWidth=[(1, 55), (2, 300)])
        cmds.text('  Decay: ')
        self.decaySlider = cmds.floatSliderGrp('decaySlider', field=True, precision=3, fmn=1, fmx=1.9, min= 1, max=1.9, value=1.2, height=25, width=180, dragCommand=self.updateDecay, sbm=self.sbmDecaySlider)
        cmds.setParent('..')
        cmds.columnLayout(columnAttach=('both',25),rowSpacing=5, columnWidth=self.windowWidth-5)
        cmds.button( label='BAKE',width=119 , height=30, bgc=(0.9,.569,0.1), command=self.springBakeFromMenu, sbm=self.sbmBake )
        cmds.setParent('..')
        cmds.rowLayout(numberOfColumns=2, columnAttach=(1, 'right', 0), columnWidth=[(1, 65), (2, 300)])
        cmds.text(label='')
        self.bakeOption = cmds.checkBox(label='Bake to Anim Layer', value=self.bakeVar)
        cmds.setParent('..')
        cmds.columnLayout(columnAttach=('both',25),rowSpacing=5, columnWidth=self.windowWidth-5)
        cmds.button( label='CLEAR',width=119 , height=30, bgc=(0.7,0.7,0.7),command=self.clear, sbm=self.sbmClear )
        cmds.button(label='SEND TO SHELF',width=120 , height=30, bgc=(0.5,.7,.7),command= self.showPresetUI, sbm=self.sbmSendToShelf)
        cmds.button(label='HELP',bgc=(0.4,0.7,0.7),width=120,height=30)
        cmds.popupMenu(button=1)
        #cmds.menuItem(label='Video Tutorial', command=self.videoTutorialLink)
        cmds.menuItem(label='More Tools', command=self.gumroadLink)
        cmds.menuItem(label='Check for Updates', command=self.checkForUpdates)
        cmds.menuItem(label='About', command=self.aboutDialog)
        cmds.setParent('..')
        cmds.columnLayout(columnAttach=('both', 25),rowSpacing=7, columnWidth=150)
        cmds.button(label="by @luismiherrera",height=15,width=self.windowWidth-55, command = self.twitterLink, bgc=(random.random()*0.5,random.random()*0.5,random.random()*0.5))#font="obliqueLabelFont",
        cmds.text(label='', height=1)
        cmds.showWindow(LMspringWindow)

        if(self.units!='cm'):
            unitsInCm = (cmds.convertUnit(1, fromUnit=self.units, toUnit='cm'))
            self.modifier = float(unitsInCm[:-2])

        cmds.setFocus("MayaWindow")

        self.checkForUpdatesAtStart()

#lmspring = LMspring()
#lmspring.showUI()