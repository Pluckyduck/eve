#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/incursionSvc.py
from service import Service
import uicls
import blue
import uthread
from pychartdir import XYChart, Transparent, PNG
import os
import taleCommon
import trinity
import audio2
import localization
import localizationUtil
INCURSION_CHAT_WARNING_DELAY = 20
INCURSION_CHAT_CLOSE_DELAY = 120
WHITE = 16777215
BLACK = 0
GRAY = 8947848
DARKGRAY = 4473924
PLOT_OFFSET = 50
PLOT_RIGHT_MARGIN = 8
PLOT_BOTTOM_MARGIN = 45
LEGEND_OFFSET = 18
COLOR_HIGH_SEC = 34816
COLOR_LOW_SEC = 13404160
COLOR_NULL_SEC = 16711680
VISUAL_STYLE_FADE_TIME = 5.0 * const.SEC
INCURSION_CLASS_ID = 2

class IncursionSvc(Service):
    __guid__ = 'svc.incursion'
    __notifyevents__ = ['OnTaleStart',
     'OnTaleEnd',
     'OnSessionChanged',
     'OnTaleData',
     'OnLoadScene']

    def Run(self, *args):
        Service.Run(self, *args)
        self.incursionData = None
        self.currentVisualStyleIntensity = 0.0
        self.targetVisualStyleIntensity = 0.0
        self.isFadingVisualStyle = False
        self.visualStyleEnabled = False
        self.enableSoundOverrides = False
        self.enablingGodRays = False
        self.stationAudioPlaying = False
        self.addStationSoundThreadRunning = False
        self.isDisablingHud = False
        self.isActivatingHud = False
        self.constellationForJoinedTaleID = {}
        self.waitingIncursionChannelTaleID = set()
        self.rewardsByID = {}
        self.soundUrlByKey = {'hangar': 10004,
         const.groupStation: 10007,
         const.groupAsteroidBelt: 10003,
         'enterSystem': 10005}

    def OnTaleData(self, solarSystemID, data):
        for taleData in data.itervalues():
            self.StartIncursion(taleData, fadeEffect=False, reason='Entered incursion system')

    def OnTaleStart(self, data):
        self.StartIncursion(data, fadeEffect=True, reason='Tale just started')

    def StartIncursion(self, data, fadeEffect = False, reason = None):
        if data.templateClassID == INCURSION_CLASS_ID:
            self.LogInfo('Starting the incursion UI for tale', data.taleID, '. Reason:', reason)
            self.incursionData = data
            self.ActivateHud(data.severity, taleCommon.CalculateDecayedInfluence(data.influenceData), data.hasBoss, fadeEffect)
            self.JoinIncursionChat(data.taleID)
            soundURL = self.GetSoundUrlByKey('enterSystem')
            if soundURL is not None:
                sm.GetService('audio').SendUIEvent(soundURL)
            if session.stationid is not None:
                self.AddIncursionStationSoundIfApplicable()

    def OnTaleEnd(self, taleID):
        self.LogInfo('OnTaleEnd', taleID)
        self.DisableHud(fadeEffect=True)
        self.incursionData = None
        sm.GetService('infoPanel').UpdateIncursionsPanel()
        self.StartTimeoutOfIncursionChat(taleID)

    def OnSessionChanged(self, isremote, sess, change):
        for taleID in self.constellationForJoinedTaleID:
            self.StartTimeoutOfIncursionChat(taleID)

        if 'solarsystemid2' in change:
            if self.incursionData is None or sess.solarsystemid2 not in self.incursionData.incursedSystems:
                self.DisableHud(fadeEffect=True)
        if 'stationid' in change:
            self.stationAudioPlaying = False
            oldStationID, newStationID = change['stationid']
            if newStationID != None:
                self.AddIncursionStationSoundIfApplicable()

    def OnLoadScene(self):
        if self.incursionData is not None:
            if session.solarsystemid2 not in self.incursionData.incursedSystems:
                self.incursionData = None
                self.DisableHud(fadeEffect=False)
                sm.GetService('infoPanel').UpdateIncursionsPanel()

    def DisableHud(self, fadeEffect = False, ignoreIsActivatingHud = False):
        if self.isDisablingHud:
            return
        try:
            self.LogInfo('Disabling incursion HUD')
            self.isDisablingHud = True
            while self.isActivatingHud and not ignoreIsActivatingHud:
                blue.pyos.synchro.Yield()

            if not fadeEffect:
                self.SetVisualStyleIntensity(0.0)
            self.SetTargetVisualStyleIntensity(0.0)
            self.enableSoundOverrides = False
        finally:
            self.isDisablingHud = False

    def ActivateHud(self, severity, influence, hasBoss, fadeEffect):
        if self.isActivatingHud:
            return
        try:
            self.LogInfo('Activating incursion HUD')
            self.isActivatingHud = True
            self.DisableHud(fadeEffect=fadeEffect, ignoreIsActivatingHud=True)
            while self.isDisablingHud:
                blue.pyos.synchro.Yield()

            self.EnableVisualStyle()
            if not fadeEffect:
                self.SetVisualStyleIntensity(1.0)
            self.SetTargetVisualStyleIntensity(1.0)
            self.enableSoundOverrides = True
            sm.GetService('infoPanel').UpdateIncursionsPanel()
        finally:
            self.isActivatingHud = False

    def FadeVisualStyle_Worker(self):
        self.LogInfo('Fade Visual Style Worker starting. Fading from', self.currentVisualStyleIntensity, 'to', self.targetVisualStyleIntensity)
        lastIntensityUpdateTime = blue.os.GetWallclockTime()
        self.isFadingVisualStyle = True
        while self.isFadingVisualStyle:
            difference = self.targetVisualStyleIntensity - self.currentVisualStyleIntensity
            if abs(difference) < 0.01:
                break
            currentTime = blue.os.GetWallclockTime()
            adjustment = float(currentTime - lastIntensityUpdateTime) / VISUAL_STYLE_FADE_TIME
            lastIntensityUpdateTime = currentTime
            if difference > 0.0:
                self.currentVisualStyleIntensity += adjustment
                if self.currentVisualStyleIntensity > self.targetVisualStyleIntensity:
                    break
            else:
                self.currentVisualStyleIntensity -= adjustment
                if self.currentVisualStyleIntensity < self.targetVisualStyleIntensity:
                    break
            self.SetVisualStyleIntensity(self.currentVisualStyleIntensity)
            blue.pyos.synchro.Yield()

        self.isFadingVisualStyle = False
        self.SetVisualStyleIntensity(self.targetVisualStyleIntensity)
        if abs(self.targetVisualStyleIntensity) < 0.01:
            self.DisableVisualStyle()
        self.LogInfo('Fade Visual Style Worker has stopped')

    def SetTargetVisualStyleIntensity(self, value):
        self.LogInfo('Visual style intensity target set to', value)
        self.targetVisualStyleIntensity = value
        if not self.isFadingVisualStyle and abs(self.targetVisualStyleIntensity - self.currentVisualStyleIntensity) > 0.01:
            uthread.new(self.FadeVisualStyle_Worker).context = 'incursionSvc::FadeVisualStyle_Worker'

    def SetVisualStyleIntensity(self, value):
        self.currentVisualStyleIntensity = value
        sceneManager = sm.GetService('sceneManager')
        scene = sceneManager.GetRegisteredScene('default')
        ppJob = sceneManager.GetFiSPostProcessingJob()
        ppJob.SetPostProcessVariable('incursionOverlay', 'Influence', value)
        if getattr(scene, 'sunBall', None) is not None:
            scene.sunBall.SetGodRaysIntensity(value)

    def EnableVisualStyle(self):
        self.LogInfo('Visual style enabled')
        sceneManager = sm.GetService('sceneManager')
        scene = sceneManager.GetRegisteredScene('default')
        ppJob = sceneManager.GetFiSPostProcessingJob()
        ppJob.AddPostProcess('incursionOverlay', 'res:/dx9/scene/postprocess/sanshaInfest.red', key='default')
        self.useGodRays = True
        uthread.new(self.EnableGodRaysThread)
        self.SetVisualStyleIntensity(0.0)
        self.visualStyleEnabled = True

    def EnableGodRaysThread(self):
        sceneManager = sm.GetService('sceneManager')
        if self.enablingGodRays:
            return
        try:
            self.enablingGodRays = True
            count = 20
            systemItems = sm.GetService('systemmap').GetSolarsystemData(self.incursionData.locationID)
            sunIDs = [ item.itemID for item in systemItems if item.groupID == const.groupSun ]
            while self.useGodRays and count:
                if session.solarsystemid == self.incursionData.locationID:
                    try:
                        scene = sceneManager.GetRegisteredScene('default')
                        if getattr(scene, 'sunBall', None) is not None and scene.sunBall.id in sunIDs:
                            scene.sunBall.EnableGodRays(True)
                            self.LogInfo('godray enabled solarsystem', session.solarsystemid)
                            break
                    except:
                        self.LogInfo('failed to enable godrays')

                blue.pyos.synchro.SleepWallclock(250)
                count -= 1

        finally:
            self.enablingGodRays = False

    def DisableVisualStyle(self):
        self.LogInfo('Visual style disabled')
        sceneManager = sm.GetService('sceneManager')
        scene = sceneManager.GetRegisteredScene('default')
        ppJob = sceneManager.GetFiSPostProcessingJob()
        ppJob.RemovePostProcess('incursionOverlay')
        self.useGodRays = False
        if getattr(scene, 'sunBall', None) is not None:
            scene.sunBall.EnableGodRays(False)
        self.visualStyleEnabled = False

    def _EndTimeoutOfIncursionChat(self, taleID):
        if taleID in self.waitingIncursionChannelTaleID:
            self.waitingIncursionChannelTaleID.remove(taleID)

    def IsTaleInTheCurrentSystem(self, taleID):
        if self.incursionData is not None:
            if self.incursionData.taleID == taleID:
                return True
        return False

    def IsIncursionActive(self):
        if self.incursionData is not None:
            return self.incursionData.templateClassID == INCURSION_CLASS_ID
        return False

    def GetActiveIncursionData(self):
        return self.incursionData

    def TimeoutOfIncursionChat_Thread(self, taleID):
        lsc = sm.GetService('LSC')
        blue.pyos.synchro.SleepWallclock(INCURSION_CHAT_WARNING_DELAY * 1000)
        if self.IsTaleInTheCurrentSystem(taleID):
            self._EndTimeoutOfIncursionChat(taleID)
            return
        window = lsc.GetChannelWindow(('incursion' + str(taleID), taleID))
        if window:
            window.Speak(localization.GetByLabel('UI/Incursion/LeaveChat', minutesRemaining=INCURSION_CHAT_CLOSE_DELAY / 60), const.ownerSystem)
        blue.pyos.synchro.SleepWallclock(INCURSION_CHAT_CLOSE_DELAY * 1000)
        if self.IsTaleInTheCurrentSystem(taleID):
            self._EndTimeoutOfIncursionChat(taleID)
            return
        lsc.LeaveChannel([('incursion' + str(taleID), taleID)])
        if taleID in self.constellationForJoinedTaleID:
            del self.constellationForJoinedTaleID[taleID]
        self._EndTimeoutOfIncursionChat(taleID)

    def StartTimeoutOfIncursionChat(self, taleID):
        if taleID not in self.waitingIncursionChannelTaleID:
            self.waitingIncursionChannelTaleID.add(taleID)
            uthread.new(self.TimeoutOfIncursionChat_Thread, taleID).context = 'IncursionSvc::StartTimeoutOfIncursionChat'

    def JoinIncursionChat(self, taleID):
        channelID = ('incursion' + str(taleID), taleID)
        lsc = sm.GetService('LSC')
        lsc.JoinChannel([channelID])
        if taleID not in self.constellationForJoinedTaleID:
            self.constellationForJoinedTaleID[taleID] = session.constellationid
            window = lsc.GetChannelWindow(channelID)
            if window:
                constellationName = cfg.evelocations.Get(session.constellationid).name
                window.Speak(localization.GetByLabel('UI/Incursion/Announcement', constellationName=constellationName), const.ownerSystem)

    def GetConstellationNameFromTaleIDForIncursionChat(self, taleID):
        if taleID in self.constellationForJoinedTaleID:
            return cfg.evelocations.Get(self.constellationForJoinedTaleID[taleID]).name
        return ''

    def GetDelayedRewardsByGroupIDs(self, rewardGroupIDs):
        rewardGroupIDs.sort()
        rewardsByRewardGroupID = sm.RemoteSvc('rewardMgr').GetDelayedRewardsByGroupIDs(tuple(rewardGroupIDs))
        return rewardsByRewardGroupID

    def GetRewardData(self, rewardID):
        reward = self.rewardsByID.get(rewardID, None)
        if not reward:
            reward = sm.RemoteSvc('rewardMgr').GetRewardData(rewardID)
        return reward

    def GetMaxRewardValue(self, rewardTables, rewardTypeID):
        largestValue = 0
        for r in rewardTables:
            if r.rewardTypeID == rewardTypeID:
                largestValue = max((e.quantity for e in r.entries))

        return largestValue

    def GetMaxRewardValueByID(self, rewardID, rewardTypeID):
        reward = self.GetRewardData(rewardID)
        largestValue = 0
        for rewardCriteria, rewardTables in reward.immediateRewards.iteritems():
            largestValue = self.GetMaxRewardValue(rewardTables, rewardTypeID)

        for rewardCriteria, rewardTables in reward.delayedRewards.iteritems():
            largestValue = max(largestValue, self.GetMaxRewardValue(rewardTables, rewardTypeID))

        return largestValue

    def GetMaxRewardPlayerCount(self, rewardTables):
        return max((table.entries[-1].playerCount for table in rewardTables))

    def GetMinRewardPlayerCount(self, rewardTables):
        return min((table.entries[0].playerCount for table in rewardTables))

    def GetQuantityForCount(self, rewardTable, count):
        quantity = 0
        for entry in rewardTable.entries:
            if entry.playerCount <= count:
                quantity = entry.quantity
            else:
                break

        return quantity

    def DoRewardChart(self, rewardID, size, icon):
        path = 'cache://Pictures/Rewards/rewardchart2_%s_%d_%d.png' % (session.languageID, size, rewardID)
        res = blue.ResFile()
        try:
            if res.Open(path):
                icon.LoadTexture(path)
                icon.SetRect(0, 0, size, size)
            else:
                uthread.new(self.DoRewardChart_Thread, rewardID, size, icon).context = 'DoRewardChart'
        finally:
            res.Close()

    def DoRewardChart_Thread(self, rewardID, size, icon):
        reward = self.GetRewardData(rewardID)
        maxRewardValue = 0
        minPlayerCount = 0
        maxPlayerCount = 0
        allSecurityBandTable = None
        lowSecurityBandTable = None
        highSecurityBandTable = None
        for rewardCriteria, rewardTables in reward.immediateRewards.iteritems():
            if not rewardTables:
                continue
            if rewardCriteria == const.rewardCriteriaAllSecurityBands:
                maxRewardValue = self.GetMaxRewardValue(rewardTables, const.rewardTypeISK)
                minPlayerCount = self.GetMinRewardPlayerCount(rewardTables)
                maxPlayerCount = self.GetMaxRewardPlayerCount(rewardTables)
                allSecurityBandTable = rewardTables[0]
                break
            if rewardCriteria == const.rewardCriteriaHighSecurity:
                highSecurityBandTable = rewardTables[0]
            elif rewardCriteria == const.rewardCriteriaLowSecurity:
                lowSecurityBandTable = rewardTables[0]
            else:
                continue
            maxRewardValue = max(maxRewardValue, self.GetMaxRewardValue(rewardTables, const.rewardTypeISK))
            minPlayerCount = min(minPlayerCount, self.GetMinRewardPlayerCount(rewardTables))
            maxPlayerCount = max(maxPlayerCount, self.GetMaxRewardPlayerCount(rewardTables))

        scale = 1.0 / maxRewardValue
        majorTick = (maxPlayerCount - minPlayerCount) / 4
        data = []
        labels = []
        for x in xrange(minPlayerCount, maxPlayerCount + 1):
            if allSecurityBandTable is not None:
                quantity = self.GetQuantityForCount(allSecurityBandTable, x) * scale
                data.append(quantity)
            else:
                quantityHigh = self.GetQuantityForCount(highSecurityBandTable, x) * scale
                quantityLow = self.GetQuantityForCount(lowSecurityBandTable, x) * scale
                data.append((quantityHigh, quantityLow))
            labels.append(str(x))

        chart = XYChart(size, size, BLACK, GRAY, False)
        chart.setPlotArea(PLOT_OFFSET, PLOT_OFFSET, size - PLOT_OFFSET - PLOT_RIGHT_MARGIN, size - PLOT_OFFSET - PLOT_BOTTOM_MARGIN, DARKGRAY, -1, -1, GRAY, Transparent)
        if localizationUtil.GetLanguageID() == localization.LOCALE_SHORT_ENGLISH:
            font = 'arial.ttf'
            titleFont = 'arialbd.ttf'
        else:
            font = titleFont = sm.GetService('font').GetFontDefault()
        chart.addLegend(LEGEND_OFFSET, LEGEND_OFFSET, 0, font, 8).setBackground(Transparent)
        legend = chart.getLegend()
        legend.setFontColor(WHITE)
        chart.addTitle(localization.GetByLabel('UI/Incursion/Reward/Title'), titleFont, 12, WHITE).setBackground(Transparent)
        yAxis = chart.yAxis()
        yAxis.setTitle(localization.GetByLabel('UI/Incursion/Reward/PayoutMultiplier'), font, 10, WHITE)
        yAxis.setColors(GRAY, WHITE)
        yAxis.setLinearScale(0, 1.02, 0.5, 0.25)
        xAxis = chart.xAxis()
        xAxis.setLabels(labels)
        xAxis.setLabelStep(majorTick)
        xAxis.setColors(GRAY, WHITE)
        xAxis.setTitle(localization.GetByLabel('UI/Incursion/Reward/NumberPilots'), font, 9, WHITE)
        layer = chart.addLineLayer2()
        layer.setLineWidth(1)
        if allSecurityBandTable is not None:
            layer.addDataSet(data, COLOR_HIGH_SEC, localization.GetByLabel('UI/Common/Ratio'))
        else:
            dataHigh, dataLow = zip(*data)
            layer.addDataSet(dataHigh, COLOR_HIGH_SEC, localization.GetByLabel('UI/Common/HighSec'))
            layer.addDataSet(dataLow, COLOR_NULL_SEC, localization.GetByLabel('UI/Common/LowNullSec'))
        directory = os.path.normpath(os.path.join(blue.paths.ResolvePath(u'cache:/'), 'Pictures', 'Rewards'))
        if not os.path.exists(directory):
            os.makedirs(directory)
        pictureName = 'rewardchart2_%s_%d_%d.png' % (session.languageID, size, rewardID)
        resPath = u'cache:/Pictures/Rewards/' + pictureName
        path = os.path.join(directory, pictureName)
        imageBuffer = chart.makeChart2(PNG)
        f = open(path, 'wb')
        f.write(imageBuffer)
        f.close()
        icon.LoadTexture(resPath)
        icon.SetRect(0, 0, size, size)

    def GetSoundUrlByKey(self, key):
        if self.enableSoundOverrides == False:
            return
        soundID = self.soundUrlByKey.get(key, None)
        if soundID is not None:
            soundRecord = cfg.sounds.GetIfExists(soundID)
            if soundRecord is None:
                self.LogError('Unable to find a sound for key', key, 'and soundID', soundID)
                soundUrl = None
            else:
                soundUrl = soundRecord.soundFile
        else:
            soundUrl = None
        return soundUrl

    def AddIncursionStationSoundIfApplicable(self):
        if not self.addStationSoundThreadRunning and self.enableSoundOverrides:
            self.addStationSoundThreadRunning = True
            uthread.new(self.AddIncursionStationSoundIfApplicableThread).context = 'incursionSvc::AddIncursionStationSoundIfApplicableThread'

    def AddIncursionStationSoundIfApplicableThread(self):
        count = 0
        success = False
        while success == False and count < 60:
            blue.synchro.SleepWallclock(1000)
            count += 1
            if session.stationid is None:
                success = True
                break
            try:
                if not self.stationAudioPlaying:
                    scene = sm.GetService('sceneManager').GetRegisteredScene('default')
                    stationModel = scene.objects[0]
                    addedSound = self.GetSoundUrlByKey('hangar')
                    if addedSound is not None:
                        triObserver = trinity.TriObserverLocal()
                        generalAudioEntity = audio2.AudEmitter('Story_general')
                        triObserver.observer = generalAudioEntity
                        stationModel.observers.append(triObserver)
                        generalAudioEntity.SendEvent(unicode(addedSound[6:]))
                        self.stationAudioPlaying = True
                        success = True
            except:
                self.LogInfo('Could not add incursion station sound trying again in 1 second')

        if success == False:
            self.LogError('Incursion station audio could not be added after 60 tries')
        self.addStationSoundThreadRunning = False