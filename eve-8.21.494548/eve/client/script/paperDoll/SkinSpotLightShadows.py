#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/paperDoll/SkinSpotLightShadows.py
import trinity
import geo2
import paperDoll as PD
import uthread
import blue
import collections
import weakref
SPOTLIGHT_SHADOW_EFFECT = 'res:/graphics/effect/managed/interior/avatar/PortraitSpotLightShadow.fx'
SPOTLIGHT_SHADOW_EFFECT_CLOTH = 'res:/graphics/effect/managed/interior/avatar/PortraitSpotLightShadowCloth.fx'
SPOTLIGHT_SHADOW_FILTER = 'res:/Graphics/Effect/Managed/Interior/Shadows/ShadowFilter.fx'

class SkinSpotLightShadows:
    __guid__ = 'paperDoll.SkinSpotLightShadows'
    renderJob = None
    instance = None
    REUSE_ENGINE_MAPS = False
    MAX_LIGHTS = 4
    NEAR_PLANE_BIAS_SCALE = -0.015
    DEFAULT_RESOLUTION = 1024

    class MeshData:

        def __init__(self, shadowResolution, isClothMesh):
            self.isClothMesh = isClothMesh
            self.viewProjParams = collections.defaultdict(list)
            self.dataParams = collections.defaultdict(list)
            self.meshAreaShadowEffect = {}
            self.meshAreaOriginalEffect = {}
            self.shadowResolution = shadowResolution

        def __del__(self):
            PD.DestroyWeakBlueDict(self.meshAreaShadowEffect)
            PD.DestroyWeakBlueDict(self.meshAreaOriginalEffect)

        def updateParams(self, light, viewProjTransform):
            for vp in self.viewProjParams[light]:
                vp.value = viewProjTransform

            for shadowEffect in self.meshAreaShadowEffect.itervalues():
                if not shadowEffect:
                    continue
                for p in shadowEffect.parameters:
                    if p.name == 'spotlight':
                        p.value = (p.value[0],
                         p.value[1],
                         p.value[2],
                         light.radius + SkinSpotLightShadows.NEAR_PLANE_BIAS_SCALE)
                        break

            if SkinSpotLightShadows.REUSE_ENGINE_MAPS:
                for map in self.maps[light]:
                    map.SetResource(light.GetShadowTextureRes())

        def createEffectParamsForLight(self, effect, index, light, shadowMapRenderTarget, debugNoFiltering):
            map = PD.SetOrAddMap(effect, 'spotLightMap' + str(index))
            map.SetResource(trinity.TriTextureRes(shadowMapRenderTarget))
            if SkinSpotLightShadows.REUSE_ENGINE_MAPS:
                self.maps[light].append(map)
            map = PD.SetOrAddMap(effect, 'Noisemap')
            map.resourcePath = 'res:/texture/global/noise.png'
            viewProj = PD.FindOrAddMat4(effect, 'spotLightViewProj' + str(index))
            self.viewProjParams[light].append(viewProj)
            lightData = PD.FindOrAddVec4(effect, 'spotLightData' + str(index))
            lightData.value = (1.0,
             1.0 / self.shadowResolution,
             float(debugNoFiltering),
             0)
            self.dataParams[light].append(lightData)
            effect.RebuildCachedData()

        def createMeshAreaParams(self, meshArea, isDecal, isCloth = False, isTranslucent = False):
            shadowEffect = trinity.Tr2Effect()
            shadowEffect.effectFilePath = SPOTLIGHT_SHADOW_EFFECT if not isCloth else SPOTLIGHT_SHADOW_EFFECT_CLOTH
            v = trinity.Tr2Vector4Parameter()
            v.name = 'spotlight'
            v.value = (float(isDecal),
             1.0 / self.shadowResolution,
             float(isTranslucent),
             1)
            shadowEffect.parameters.append(v)
            effect = None
            if hasattr(meshArea, 'effect') and meshArea.effect:
                effect = meshArea.effect
            elif hasattr(meshArea, 'effectReversed') and meshArea.effectReversed:
                effect = meshArea.effectReversed
            if type(effect) is not trinity.Tr2Effect:
                return
            if effect and isDecal:
                for p in effect.parameters:
                    if p.name == 'TransformUV0':
                        v = trinity.Tr2Vector4Parameter()
                        v.name = p.name
                        v.value = p.value
                        shadowEffect.parameters.append(v)
                    elif p.name == 'CutMaskInfluence':
                        v = trinity.Tr2FloatParameter()
                        v.name = p.name
                        v.value = p.value
                        shadowEffect.parameters.append(v)

                for r in effect.resources:
                    if r.name == 'DiffuseMap' or r.name == 'CutMaskMap':
                        t = trinity.TriTexture2DParameter()
                        t.name = r.name
                        t.SetResource(r.resource)
                        shadowEffect.resources.append(t)

            shadowEffect.RebuildCachedData()
            if effect:
                PD.AddWeakBlue(self, 'meshAreaShadowEffect', meshArea, shadowEffect)
                PD.AddWeakBlue(self, 'meshAreaOriginalEffect', meshArea, meshArea.effect)

        def inhibitShadows(self, meshArea):
            PD.AddWeakBlue(self, 'meshAreaShadowEffect', meshArea, None)
            PD.AddWeakBlue(self, 'meshAreaOriginalEffect', meshArea, meshArea.effect)

        def applyShadowEffect(self):
            if self.meshAreaShadowEffect:
                for meshArea, effect in self.meshAreaShadowEffect.iteritems():
                    if meshArea and meshArea.object:
                        meshArea.object.effect = effect

        def applyOriginalEffect(self):
            if self.meshAreaOriginalEffect:
                for meshArea, effect in self.meshAreaOriginalEffect.iteritems():
                    if meshArea and meshArea.object:
                        meshArea.object.effect = effect

    @staticmethod
    def watchdog(weakSelf):
        while True:
            blue.synchro.SleepWallclock(2000)
            selfRef = weakSelf()
            if selfRef is None:
                return
            if len(selfRef.scene.lights) != len(selfRef.lights):
                selfRef.RefreshLights()

    def RefreshLights(self):
        meshes = self.meshes
        self.CreateRenderJobsForScene()
        for meshRef in meshes.iterkeys():
            if meshRef.object:
                self.CreateEffectParamsForMesh(meshRef.object, isClothMesh=meshes[meshRef].isClothMesh)

        for instance in PD.SkinLightmapRenderer.instances:
            if instance():
                instance().Refresh(immediateUpdate=True)

    def __init__(self, scene, size = None, format = None, applyBlur = True, debugVisualize = False, debugNoFiltering = False, lightFilter = None):
        size = size if size else SkinSpotLightShadows.DEFAULT_RESOLUTION
        trinity.device.RegisterResource(self)
        self.scene = scene
        self.meshes = {}
        self.autoOptimizeFrustum = True
        self.lightFilter = lightFilter
        if self.scene is not None and hasattr(self.scene, 'updateShadowCubeMap'):
            self.oldShadowsEnabled = self.scene.updateShadowCubeMap
            self.scene.updateShadowCubeMap = False
        self.format = format if format else trinity.PIXEL_FORMAT.R32_FLOAT
        self.width = self.height = size
        self.lights = []
        self.jobs = {}
        self.RTs = {}
        self.debugVisualize = debugVisualize
        self.debugNoFiltering = debugNoFiltering
        self.applyBlur = applyBlur
        if self.scene is not None:
            self.watchdogThread = uthread.new(SkinSpotLightShadows.watchdog, weakref.ref(self))
        else:
            self.watchdogThread = None
        self.shiftU = 0
        self.shiftV = 0
        if trinity.device.GetRenderingPlatformID() == 1:
            self.shiftU = 0.5 / self.width
            self.shiftV = 0.5 / self.height
        self.uvAdjustMatrix = ((0.5, 0, 0, 0),
         (0, -0.5, 0, 0),
         (0, 0, 1, 0),
         (0.5 + self.shiftU,
          0.5 + self.shiftV,
          0,
          1))

    def SetShadowMapResolution(self, size):
        self.width = self.height = size
        self.uvAdjustMatrix = ((0.5, 0, 0, 0),
         (0, -0.5, 0, 0),
         (0, 0, 1, 0),
         (0.5 + self.shiftU,
          0.5 + self.shiftV,
          0,
          1))
        self.RefreshLights()

    def GetShadowMapResolution(self):
        return self.width

    def __del__(self):
        self.Clear(killThread=True)
        if self.scene is not None and hasattr(self.scene, 'updateShadowCubeMap'):
            self.scene.updateShadowCubeMap = self.oldShadowsEnabled

    @staticmethod
    def SetupForCharacterCreator(scene, shadowMapSize = None, lightFilter = None):
        if scene is None:
            return
        if SkinSpotLightShadows.instance is not None:
            if scene == SkinSpotLightShadows.instance.scene:
                SkinSpotLightShadows.instance.RefreshLights()
                return
            SkinSpotLightShadows.instance.Clear(killThread=True)
            SkinSpotLightShadows.instance = None
        SkinSpotLightShadows.instance = SkinSpotLightShadows(scene, size=shadowMapSize, lightFilter=lightFilter)
        SkinSpotLightShadows.instance.CreateRenderJobsForScene()
        SkinSpotLightShadows.SetupFloorDropShadow(scene)
        for dynamic in scene.dynamics:
            if dynamic.__typename__ == 'Tr2IntSkinnedObject':
                SkinSpotLightShadows.instance.SetupSkinnedObject(dynamic, createJobs=False)

    def SetupSkinnedObject(self, object, createJobs = True):
        if createJobs:
            self.CreateRenderJobsForScene()
        if object and object.visualModel:
            for mesh in object.visualModel.meshes:
                self.CreateEffectParamsForMesh(mesh, False)

            for mesh in object.clothMeshes:
                self.CreateEffectParamsForMesh(mesh, True)

            for instance in PD.SkinLightmapRenderer.instances:
                if instance():
                    instance().Refresh(immediateUpdate=True)

    def OnInvalidate(self, level):
        if not hasattr(self, 'deviceLostMeshes'):
            self.deviceLostMeshes = self.meshes
            self.Clear(killThread=True)

    def OnCreate(self, dev):
        self.meshes = self.deviceLostMeshes
        del self.deviceLostMeshes
        self.RefreshLights()

    def RemoveRenderJobs(self):
        if SkinSpotLightShadows.renderJob is not None and SkinSpotLightShadows.renderJob.object is not None:
            SkinSpotLightShadows.renderJob.object.steps.removeAt(-1)
        for jobs in self.jobs.values():
            for rj in jobs:
                rj.UnscheduleRecurring()

        self.jobs = {}

    def Clear(self, killThread = False):
        if killThread and self.watchdogThread is not None:
            self.watchdogThread.kill()
            self.watchdogThread = None
        self.RemoveRenderJobs()
        self.lights = []
        self.RTs = {}
        PD.DestroyWeakBlueDict(self.meshes)
        self.meshes = {}

    def ComputeProjectionMatrix(self, projection, light, viewmat):
        fov = light.coneAlphaOuter * 3.1415927 / 90.0
        projection.PerspectiveFov(fov, 1.0, 0.1, light.radius)
        if not self.scene or not self.autoOptimizeFrustum:
            return
        model = None
        for dynamic in self.scene.dynamics:
            if dynamic.__typename__ == 'Tr2IntSkinnedObject':
                if model is not None:
                    return
                model = dynamic

        if model is None:
            return
        VP = geo2.MatrixMultiply(viewmat, projection.transform)
        m = model.transform
        mm = ((m._11,
          m._12,
          m._13,
          m._14),
         (m._21,
          m._22,
          m._23,
          m._24),
         (m._31,
          m._32,
          m._33,
          m._34),
         (m._41,
          m._42,
          m._43,
          m._44))
        obb = model.GetClippedWorldBoundingObb(mm)

        def getPoint(i):
            p = obb[3]
            x = obb[0]
            y = obb[1]
            z = obb[2]
            size = obb[4]
            p = geo2.Vec3Add(p, geo2.Vec3Scale(x, size[0] if i & 1 else -size[0]))
            p = geo2.Vec3Add(p, geo2.Vec3Scale(y, size[1] if i & 2 else -size[1]))
            p = geo2.Vec3Add(p, geo2.Vec3Scale(z, size[2] if i & 4 else -size[2]))
            return p

        maxx = -1.0
        maxy = -1.0
        minx = 1.0
        miny = 1.0
        pClip = []
        for i in xrange(8):
            p = getPoint(i)
            pClip.append((p[0],
             p[1],
             p[2],
             1))

        pClip = geo2.Vec4TransformArray(pClip, VP)
        for pp in pClip:
            if pp[3] < 0.0001:
                continue
            pp = (pp[0] / pp[3], pp[1] / pp[3], pp[2] / pp[3])
            minx = min(minx, pp[0])
            miny = min(miny, pp[1])
            maxx = max(maxx, pp[0])
            maxy = max(maxy, pp[1])

        def clip(x):
            if x < -1.0:
                return -1.0
            if x > 1.0:
                return 1.0
            return x

        minx = clip(minx)
        miny = clip(miny)
        maxx = clip(maxx)
        maxy = clip(maxy)
        if minx >= maxx or miny >= maxy:
            return
        scalex = 2.0 / (maxx - minx)
        scaley = 2.0 / (maxy - miny)
        biasx = (minx + maxx) / (minx - maxx)
        biasy = (miny + maxy) / (miny - maxy)
        bias = ((scalex,
          0,
          0,
          0),
         (0,
          scaley,
          0,
          0),
         (0, 0, 1, 0),
         (biasx,
          biasy,
          0,
          1))
        projM = geo2.MatrixMultiply(projection.transform, bias)
        projection.CustomProjection(projM)

    def UpdateViewProjForLight(self, stepView, stepProj, light, effectValue):
        eye = light.position
        at = geo2.Add(eye, light.coneDirection)
        up = (0, 0, 1)
        if SkinSpotLightShadows.REUSE_ENGINE_MAPS:
            VP = light.GetViewProjMatrix()
        else:
            if effectValue:
                effectValue.value = (0,
                 0,
                 0,
                 light.radius)
            viewmat = geo2.MatrixLookAtRH(eye, at, up)
            self.ComputeProjectionMatrix(stepProj.projection, light, viewmat)
            stepView.view.transform = viewmat
            VP1 = geo2.MatrixMultiply(viewmat, stepProj.projection.transform)
            VP = geo2.MatrixMultiply(VP1, self.uvAdjustMatrix)
        VPT = geo2.MatrixTranspose(VP)
        for meshData in self.meshes.itervalues():
            meshData.updateParams(light, VPT)

    def CreateRenderJobsForLight(self, light):
        self.lights.append(light)
        if not SkinSpotLightShadows.REUSE_ENGINE_MAPS:
            light.shadowCasterTypes = 0
        else:
            light.shadowResolution = 1024
        ignoreLight = False
        if self.lightFilter is not None and light.name not in self.lightFilter:
            ignoreLight = True
        elif len(self.lights) > SkinSpotLightShadows.MAX_LIGHTS or light.coneAlphaOuter > 89:
            ignoreLight = True
        if ignoreLight:
            light.importanceScale = 0
            light.importanceBias = -9999
            light.shadowCasterTypes = 0
            return
        light.importanceScale = 0
        light.importanceBias = -len(self.lights)
        if SkinSpotLightShadows.REUSE_ENGINE_MAPS:
            self.RTs[light] = light.GetShadowTextureRes()
            rj = trinity.CreateRenderJob('render shadowmap ' + str(light))
            self.jobs[light] = [rj]
            cb = trinity.TriStepPythonCB()
            cb.name = 'UpdateViewProjForLight'
            cb.SetCallback(lambda : self.UpdateViewProjForLight(None, None, light, None))
            rj.steps.append(cb)
            rj.ScheduleRecurring()
            return
        rj = trinity.CreateRenderJob('render shadowmap ' + str(light))
        renderTarget = None
        while self.width > 8:
            renderTarget = trinity.Tr2RenderTarget(self.width, self.height, 1, self.format)
            if renderTarget is None or not renderTarget.isValid:
                renderTarget = None
                self.width /= 2
                self.height /= 2
                PD.Yield()
            else:
                break

        self.RTs[light] = renderTarget
        depthStencil = None
        while self.width > 8:
            depthStencil = trinity.Tr2DepthStencil(self.width, self.height, trinity.DEPTH_STENCIL_FORMAT.D24S8)
            if depthStencil is None or not depthStencil.isValid:
                depthStencil = None
                self.width /= 2
                self.height /= 2
                PD.Yield()
            else:
                break

        if not renderTarget or not depthStencil or not renderTarget.isValid or not depthStencil.isValid:
            return
        v = None
        rj.PushViewport()
        rj.PushRenderTarget(renderTarget)
        rj.PushDepthStencil(depthStencil)
        clearColor = (100.0, 1.0, 1.0, 1.0)
        rj.Clear(clearColor, 1.0)
        vp = trinity.TriViewport()
        vp.x = 0
        vp.y = 0
        vp.width = self.width
        vp.height = self.height
        rj.PushProjection()
        rj.PushViewTransform()
        rj.SetViewport(vp)
        cb = trinity.TriStepPythonCB()
        cb.name = 'UpdateViewProjForLight'
        rj.steps.append(cb)
        stepProj = rj.SetProjection(trinity.TriProjection())
        stepView = rj.SetView(trinity.TriView())
        self.UpdateViewProjForLight(stepView, stepProj, light, v)
        cb.SetCallback(lambda : self.UpdateViewProjForLight(stepView, stepProj, light, v))

        def applyVisualizer(doIt):
            for meshData in self.meshes.itervalues():
                if doIt:
                    meshData.applyShadowEffect()
                else:
                    meshData.applyOriginalEffect()

        cb = trinity.TriStepPythonCB()
        cb.name = 'applyVisualizer(True)'
        cb.SetCallback(lambda : applyVisualizer(True))
        rj.steps.append(cb)
        rj.RenderScene(self.scene)
        cb = trinity.TriStepPythonCB()
        cb.name = 'applyVisualizer(False)'
        cb.SetCallback(lambda : applyVisualizer(False))
        rj.steps.append(cb)
        rj.PopDepthStencil()
        rj.PopRenderTarget()
        rj.PopViewTransform().name = 'TriStepPopViewTransform Restoring state'
        rj.PopViewport()
        rj.PopProjection()
        if SkinSpotLightShadows.renderJob is not None and SkinSpotLightShadows.renderJob.object is not None:
            step = trinity.TriStepRunJob()
            step.job = rj
            SkinSpotLightShadows.renderJob.object.steps.insert(0, step)
        else:
            self.jobs[light] = [rj]
            rj.ScheduleRecurring(insertFront=True)
        if self.debugVisualize:
            rj2 = trinity.CreateRenderJob('visualize shadowmap ' + str(light))
            if light not in self.jobs:
                self.jobs[light] = [rj2]
            else:
                self.jobs[light].append(rj2)
            rj2.PushDepthStencil(None)
            size = 200
            vp2 = trinity.TriViewport()
            vp2.x = 10
            vp2.y = 10 + (size + 10) * (len(self.lights) - 1)
            vp2.width = size
            vp2.height = size
            rj2.PushViewport()
            rj2.PushProjection()
            rj2.PushViewTransform()
            rj2.SetViewport(vp2)
            rj2.SetStdRndStates(trinity.RM_FULLSCREEN)
            rj2.RenderTexture(renderTarget)
            rj2.PopViewTransform()
            rj2.PopProjection()
            rj2.PopViewport()
            rj2.PopDepthStencil()
            rj2.ScheduleRecurring()

    def CreateRenderJobsForScene(self):
        self.Clear()
        for light in self.scene.lights:
            self.CreateRenderJobsForLight(light)

    def CreateEffectParams(self, effect, meshData):
        numLight = len(self.lights)
        if numLight > SkinSpotLightShadows.MAX_LIGHTS:
            numLight = SkinSpotLightShadows.MAX_LIGHTS
        for param in effect.parameters:
            if param.name.startswith('spotLightData'):
                param.value = (0, 1, 0, 0)

        for l in xrange(numLight):
            light = self.lights[l]
            renderTarget = self.RTs.get(light, None)
            if renderTarget is not None:
                meshData.createEffectParamsForLight(effect, l, light, renderTarget, self.debugNoFiltering)

    def CreateEffectParamsForMesh(self, mesh, isClothMesh = False):
        meshData = self.MeshData(self.width, isClothMesh)

        def IsHair(mesh):
            if not hasattr(mesh, 'name'):
                return True
            if mesh.name.lower().startswith('hair'):
                return True
            return False

        def IsSkin(mesh):
            if not hasattr(mesh, 'name'):
                return False
            skinAreas = ['bottominner',
             'topinner',
             'hands',
             'feet',
             'sleeveslower/standard',
             'sleevesupper/standard']
            for sa in skinAreas:
                if mesh.name.lower().startswith(sa):
                    return True

            return False

        isTranslucent = IsHair(mesh)
        isInteriorStatic = hasattr(mesh, 'enlightenAreas')
        if isInteriorStatic:
            for areaMesh in mesh.enlightenAreas:
                meshData.createMeshAreaParams(areaMesh, isDecal=False, isTranslucent=False)

        elif not isClothMesh:
            for areaMesh in mesh.opaqueAreas:
                if not PD.IsBeard(areaMesh):
                    meshData.createMeshAreaParams(areaMesh, isDecal=False, isTranslucent=isTranslucent or PD.IsGlasses(areaMesh))
                else:
                    meshData.inhibitShadows(areaMesh)

            for areaMesh in mesh.decalAreas:
                if not PD.IsBeard(areaMesh):
                    meshData.createMeshAreaParams(areaMesh, isDecal=True, isTranslucent=isTranslucent or PD.IsGlasses(areaMesh))
                else:
                    meshData.inhibitShadows(areaMesh)

            for areaMesh in mesh.transparentAreas:
                if IsHair(mesh):
                    meshData.createMeshAreaParams(areaMesh, isDecal=True, isTranslucent=True)
                else:
                    meshData.inhibitShadows(areaMesh)

        else:
            if hasattr(mesh, 'effect') and mesh.effect and 'clothavatarhair_detailed' in mesh.effect.effectFilePath.lower():
                isTranslucent = True
            meshData.createMeshAreaParams(mesh, isDecal=True, isCloth=True, isTranslucent=isTranslucent)
        fx = PD.GetEffectsFromMesh(mesh)
        for f in fx:
            self.CreateEffectParams(f, meshData)

        for key in self.meshes.iterkeys():
            if key.object == mesh:
                self.meshes[key] = meshData
                break
        else:
            PD.AddWeakBlue(self, 'meshes', mesh, meshData)

    def CreateShadowStep(renderJob, append = True):
        shadowStep = trinity.TriStepRunJob()
        shadowStep.name = 'Spotlight shadows'
        shadowStep.job = trinity.CreateRenderJob('Render shadowmaps')
        if append:
            renderJob.steps.append(shadowStep)
        SkinSpotLightShadows.renderJob = blue.BluePythonWeakRef(shadowStep.job)
        if SkinSpotLightShadows.instance is not None:
            SkinSpotLightShadows.instance.RefreshLights()
        return shadowStep

    @staticmethod
    def SetupFloorDropShadow(scene, doYield = True):
        if scene is None or SkinSpotLightShadows.instance is None:
            return

        def SetupCurve(effect):
            doll = scene.dynamics[0]
            if doll is None:
                return
            setName = 'Dropshadow foot tracker'
            set = None
            for s in doll.curveSets:
                if s.name == setName:
                    set = s
                    set.curves.removeAt(-1)
                    set.bindings.removeAt(-1)
                    break
            else:
                set = trinity.TriCurveSet()
                set.name = setName
                doll.curveSets.append(set)

            bones = ['LeftFoot', 'RightFoot']
            for bone in bones:
                curve = trinity.Tr2BoneMatrixCurve()
                curve.skinnedObject = doll
                curve.bone = bone
                curve.name = bone
                param = PD.FindOrAddVec4(effect, bone)
                bind = trinity.TriValueBinding()
                bind.destinationObject = param
                bind.destinationAttribute = 'value'
                bind.sourceObject = curve
                bind.sourceAttribute = 'currentValue'
                bind.name = bone
                set.curves.append(curve)
                set.bindings.append(bind)

            set.Play()

        lights = scene.lights
        frontMainLightIndex = 0
        for light in lights:
            if light.name == 'FrontMain':
                frontMainLightIndex = lights.index(light)
                break

        values = [(1, 0, 0, 0),
         (0, 1, 0, 0),
         (0, 0, 1, 0),
         (0, 0, 0, 1)]
        for cell in scene.cells:
            for system in cell.systems:
                for static in system.statics:
                    if PD.SkinSpotLightShadows.instance is not None:
                        PD.SkinSpotLightShadows.instance.CreateEffectParamsForMesh(static, isClothMesh=False)
                    for area in static.enlightenAreas:
                        area.effect.effectFilePath = 'res:/Graphics/Effect/Managed/Interior/Avatar/PortraitDropShadow.fx'
                        if doYield:
                            while area.effect.effectResource.isLoading:
                                PD.Yield()

                        SetupCurve(area.effect)
                        area.effect.RebuildCachedData()
                        if frontMainLightIndex < len(values):
                            p = PD.FindOrAddVec4(area.effect, 'ShadowSelector')
                            p.value = values[frontMainLightIndex]