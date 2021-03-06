#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/paperDoll/SkinRaytracing.py
import trinity
import blue
import telemetry
import ctypes
import math
import time
import geo2
import struct
import itertools
import weakref
import uthread
import paperDoll as PD
import log
import random
mylog = log.Channel('optix', 'python')

def LogInfo(text, *args):
    for arg in args:
        text += ' ' + str(arg)

    mylog.Log(text, log.LGINFO)


def LogWarn(text, *args):
    for arg in args:
        text = text + ' ' + str(arg)

    mylog.Log(text, log.LGWARN)


class SkinRaytracingTools():
    __guid__ = 'paperDoll.SkinRaytracingTools'

    @staticmethod
    def SetOptixMatrixFromTrinity(optix, matrixName, ratio = None):
        proj = trinity.TriProjection()
        view = trinity.TriView()
        view.transform = trinity.GetViewTransform()
        proj.PerspectiveFov(trinity.GetFieldOfView(), trinity.GetAspectRatio() if ratio is None else ratio, trinity.GetFrontClip(), trinity.GetBackClip())
        projToView = geo2.MatrixInverse(proj.transform)
        viewToWorld = geo2.MatrixInverse(view.transform)
        projToWorld = geo2.MatrixMultiply(projToView, viewToWorld)
        r0 = projToWorld[0]
        r1 = projToWorld[1]
        r2 = projToWorld[2]
        r3 = projToWorld[3]
        mat = trinity.TriMatrix(r0[0], r0[1], r0[2], r0[3], r1[0], r1[1], r1[2], r1[3], r2[0], r2[1], r2[2], r2[3], r3[0], r3[1], r3[2], r3[3])
        optix.SetMatrix4x4(matrixName, mat)
        r0 = view.transform[0]
        r1 = view.transform[1]
        r2 = view.transform[2]
        r3 = view.transform[3]
        mat = trinity.TriMatrix(r0[0], r0[1], r0[2], r0[3], r1[0], r1[1], r1[2], r1[3], r2[0], r2[1], r2[2], r2[3], r3[0], r3[1], r3[2], r3[3])
        optix.SetMatrix4x4('viewTransform', mat)
        return mat

    @staticmethod
    def CreateSamplerForTexture(name, map, waitForFinish):
        rt = trinity.Tr2RenderTarget(map.width, map.height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        job = trinity.CreateRenderJob()
        job.PushRenderTarget(rt)
        job.PushDepthStencil(None)
        job.SetStdRndStates(trinity.RM_FULLSCREEN)
        job.RenderTexture(map)
        job.PopDepthStencil()
        job.PopRenderTarget()
        job.ScheduleOnce()
        if waitForFinish:
            job.WaitForFinish()
        sampler = trinity.Tr2OptixTextureSampler()
        if True:
            res = trinity.TriTextureRes()
            res.CreateAndCopyFromRenderTarget(rt)
            sampler.CreateFromTexture(res)
        else:
            sampler.CreateFromRenderTarget(rt)
        sampler.SetNormalizedIndexingMode(True)
        if True:
            return (sampler, res)
        else:
            return (sampler, rt)

    @staticmethod
    def ConvertCubeToTextures(cube):
        names = ['PX',
         'NX',
         'PY',
         'NY',
         'PZ',
         'NZ']
        viewVec = [(1, 0, 0),
         (-1, 0, 0),
         (0, 1, 0),
         (0, -1, 0),
         (0, 0, 1),
         (0, 0, -1)]
        upVec = [(0, 1, 0),
         (0, 1, 0),
         (0, 0, 1),
         (0, 0, -1),
         (0, 1, 0),
         (0, 1, 0)]
        spaceScene = trinity.EveSpaceScene()
        spaceScene.envMap1ResPath = str(cube.resourcePath)
        spaceScene.envMapScaling = (1, 1, -1)
        spaceScene.backgroundRenderingEnabled = True
        spaceScene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/bakeNebula.red')
        blue.resMan.Wait()
        node = PD.FindParameterByName(spaceScene.backgroundEffect, 'NebulaBrightness')
        if node is None:
            node = trinity.Tr2FloatParameter()
            node.name = 'NebulaBrightness'
            spaceScene.backgroundEffect.parameters.append(node)
        if node is not None:
            node.value = 100
        node = PD.FindResourceByName(spaceScene.backgroundEffect, 'NebulaMap')
        if node is None:
            node = trinity.TriTexture2DParam()
            node.name = 'NebulaMap'
            spaceScene.backgroundEffect.resources.append(node)
        node.SetResource(cube.resource)
        blue.resMan.Wait()
        mipmapped = []
        useTexture = True
        for i in xrange(len(names)):
            name = names[i]
            rt = PD.SkinLightmapRenderer.CreateRenderTarget(cube.resource.width, cube.resource.height, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM, useRT=True)
            job = trinity.CreateRenderJob(name=name)
            job.PushRenderTarget(rt)
            job.PushDepthStencil(None)
            job.Clear([(1, 0, 0),
             (0.2, 0, 0),
             (0, 1, 0),
             (0, 0.2, 0),
             (0, 0, 1),
             (0, 0, 0.2)][i], None)
            proj = trinity.TriProjection()
            proj.PerspectiveFov(math.pi * 0.5, 1, 0.1, 1000)
            view = trinity.TriView()
            view.SetLookAtPosition((0, 0, 0), viewVec[i], upVec[i])
            viewport = trinity.TriViewport(0, 0, cube.resource.width, cube.resource.height, 0.0, 1.0)
            job.SetView(view)
            job.SetProjection(proj)
            job.SetViewport(viewport)
            job.Update(spaceScene)
            job.RenderScene(spaceScene)
            job.PopDepthStencil()
            job.PopRenderTarget()
            if useTexture:
                tex = trinity.TriTextureRes(cube.resource.width, cube.resource.height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
            if True:
                job.ScheduleOnce()
                job.WaitForFinish()
                if useTexture:
                    mipmapped.append(tex)
                else:
                    mipmapped.append(rt)
            else:
                job.ScheduleRecurring()

        return (mipmapped, names)

    @staticmethod
    def FindAllTextureResourcesFromEffect(effect, scope):
        textures = {}
        samplers = []
        cubemaps = []
        if effect is not None:
            for r in effect.resources:
                if type(r) == trinity.TriTexture2DParameter and r.resource is not None:
                    textures[r.name] = r.resource
                elif type(r) == trinity.TriTextureCubeParameter and r.resource is not None:
                    if r.name in cubemaps:
                        continue
                    LogInfo('', r.name, ': Converting to individual textures')
                    cubemaps.append(r.name)
                    mipmaps, names = SkinRaytracingTools.ConvertCubeToTextures(r)
                    for i in range(len(names)):
                        if i < len(mipmaps):
                            sampler = trinity.Tr2OptixTextureSampler()
                            sampler.CreateFromTexture(mipmaps[i])
                            sampler.SetNormalizedIndexingMode(True)
                            scope.SetSampler(r.name + names[i], sampler)
                            LogInfo('No-Copy Cube Side Interop for ' + r.name + names[i])
                            samplers.append(mipmaps[i])
                            samplers.append(sampler)

        return (textures, samplers)

    @staticmethod
    def FindAllTextureResources(dynamic, scope):
        textures = {}
        samplers = []
        cubemaps = []

        def ProcessMesh(mesh):
            for area in itertools.chain(mesh.opaqueAreas, mesh.decalAreas, mesh.transparentAreas):
                newTextures, newSamplers = SkinRaytracingTools.FindAllTextureResourcesFromEffect(area.effect, scope)
                textures.update(newTextures)
                samplers.extend(newSamplers)

        if type(dynamic) == trinity.Tr2IntSkinnedObject:
            for mesh in dynamic.visualModel.meshes:
                ProcessMesh(mesh)

        elif type(dynamic) == trinity.EveShip2:
            ProcessMesh(dynamic.highDetailMesh.object)
        elif type(dynamic) == trinity.EveStation2:
            ProcessMesh(dynamic.highDetailMesh.object)
        return (textures, samplers)

    @staticmethod
    def InteropTexture(name, texture, waitForFinish, scope):
        if texture.format == trinity.PIXEL_FORMAT.B8G8R8A8_UNORM:
            sampler = trinity.Tr2OptixTextureSampler()
            sampler.CreateFromTexture(texture)
            sampler.SetNormalizedIndexingMode(True)
            scope.SetSampler(name, sampler)
            LogInfo('No-Copy Interop for', name)
            return (sampler, None)
        if texture.type == trinity.TRIRTYPE_CUBETEXTURE:
            LogInfo('Copy-Interop for cubes not supported, skipping', name)
            return
        sampler_rt = SkinRaytracingTools.CreateSamplerForTexture(name, texture, waitForFinish)
        if sampler_rt is None or len(sampler_rt) < 1:
            LogInfo('InteropTexture failed for', name)
        else:
            scope.SetSampler(name, sampler_rt[0])
            LogInfo('Interop for', name)
        return sampler_rt

    @staticmethod
    def InteropAllTexturesFromEffect(optix, effect, waitForFinish, nameTranslation = None, scope = None, cache = None):
        if scope is None:
            scope = optix
        textures, samplers = SkinRaytracingTools.FindAllTextureResourcesFromEffect(effect, scope)
        for name, texture in textures.iteritems():
            if 'spotlight' in name.lower():
                continue
            if nameTranslation is not None:
                name = nameTranslation.get(name, name)
            if cache is not None and texture in cache:
                sampler = cache[texture]
                scope.SetSampler(name, sampler[0])
                LogInfo('Interop cache for', name)
            else:
                sampler = SkinRaytracingTools.InteropTexture(name, texture, waitForFinish, scope)
                if sampler and cache is not None:
                    cache[texture] = sampler
            if sampler is not None:
                samplers.append(sampler)

        return samplers

    @staticmethod
    def InteropAllTextures(optix, dynamic, waitForFinish, nameTranslation = None, scope = None):
        if scope is None:
            scope = optix
        textures, samplers = SkinRaytracingTools.FindAllTextureResources(dynamic, scope)
        for name, texture in textures.iteritems():
            if 'spotlight' in name.lower():
                continue
            if nameTranslation is not None:
                name = nameTranslation.get(name, name)
            sampler = SkinRaytracingTools.InteropTexture(name, texture, waitForFinish, scope)
            if sampler is not None:
                samplers.append(sampler)

        return samplers

    @staticmethod
    def SafeLinearize(values):
        peak = max(1, max(values[0], max(values[1], values[2])))
        return (peak * math.pow(values[0] / peak, 2.2),
         peak * math.pow(values[1] / peak, 2.2),
         peak * math.pow(values[2] / peak, 2.2),
         values[3])

    @staticmethod
    def CopyParametersToContext(effect, instance, linearNames = None):
        for p in effect.parameters:
            if type(p) is trinity.Tr2Vector4Parameter:
                value = SkinRaytracingTools.SafeLinearize(p.value) if linearNames is not None and p.name in linearNames else p.value
                instance.SetFloat4(p.name, value[0], value[1], value[2], value[3])
            elif type(p) is trinity.TriFloatParameter or type(p) is trinity.Tr2FloatParameter:
                instance.SetFloat4(p.name, p.value, 0, 0, 0)

    @staticmethod
    def CreateBufferForLights(lights, leaveEmpty = False, preserveAlpha = False):
        bufEveLights = trinity.Tr2OptixBuffer()
        bufEveLights.CreateUserData(64, len(lights), trinity.OPTIX_BUFFER_OUTPUT, False)
        bufEveLights.MapUser()
        buffer = ''
        if leaveEmpty:
            lights = []
        for light in lights:
            innerAngle = light.coneAlphaInner
            outerAngle = light.coneAlphaOuter
            if innerAngle + 1.0 > outerAngle:
                innerAngle = outerAngle - 1.0
            innerAngle = math.cos(innerAngle * 3.1415927 / 180.0)
            outerAngle = math.cos(outerAngle * 3.1415927 / 180.0)
            coneDir = geo2.Vec3Normalize((light.coneDirection[0], light.coneDirection[1], light.coneDirection[2]))
            import struct
            buffer += struct.pack('16f', light.position[0], light.position[1], light.position[2], light.radius, math.pow(light.color[0], 2.2), math.pow(light.color[1], 2.2), math.pow(light.color[2], 2.2), light.falloff if not preserveAlpha else light.color[3], coneDir[0], coneDir[1], coneDir[2], outerAngle, innerAngle, 0, 0, 0)

        bufEveLights.SetUserDataFromStruct(buffer)
        bufEveLights.UnmapUser()
        return bufEveLights

    @staticmethod
    def CreateUInt1Buffer(optix, name):
        buffer = trinity.Tr2OptixBuffer()
        buffer.CreateUInt1(1, 1, trinity.OPTIX_BUFFER_INPUT_OUTPUT)
        buffer.Map()
        buffer.SetUserDataI(0, 0)
        buffer.Unmap()
        optix.SetBuffer(name, buffer)
        return buffer

    @staticmethod
    def matEqual(m1, m2):
        return m1._11 == m2._11 and m1._12 == m2._12 and m1._13 == m2._13 and m1._14 == m2._14 and m1._21 == m2._21 and m1._22 == m2._22 and m1._23 == m2._23 and m1._24 == m2._24 and m1._31 == m2._31 and m1._32 == m2._32 and m1._33 == m2._33 and m1._34 == m2._34 and m1._41 == m2._41 and m1._42 == m2._42 and m1._43 == m2._43 and m1._44 == m2._44

    @staticmethod
    def FuncWrapper(weakSelf, func):
        if weakSelf():
            func(weakSelf())


class OitHelper():

    def __init__(self, optix):
        self.oitAllocatorBuffer = SkinRaytracingTools.CreateUInt1Buffer(optix, 'oit_allocator')
        oitPoolBuffer = trinity.Tr2OptixBuffer()
        oitPoolBuffer.CreateUserData(64 + 112, 1048576, trinity.OPTIX_BUFFER_INPUT_OUTPUT, True)
        optix.SetBuffer('oit_pool', oitPoolBuffer)
        self.oitPoolBuffer = oitPoolBuffer

    def ResetAllocationCount(self):
        self.oitAllocatorBuffer.Map()
        self.oitAllocatorBuffer.SetUserDataI(0, 0)
        self.oitAllocatorBuffer.Unmap()

    def GetAllocationCount(self):
        self.oitAllocatorBuffer.Map()
        count = self.oitAllocatorBuffer.GetUserDataI(0)
        self.oitAllocatorBuffer.Unmap()
        return count


class RayCountHelper():

    def __init__(self, optix):
        self.rayCountBuffer = SkinRaytracingTools.CreateUInt1Buffer(optix, 'ray_count')

    def ResetCount(self):
        self.rayCountBuffer.Map()
        self.rayCountBuffer.SetUserDataI(0, 0)
        self.rayCountBuffer.Unmap()

    def GetCount(self):
        self.rayCountBuffer.Map()
        count = self.rayCountBuffer.GetUserDataI(0)
        self.rayCountBuffer.Unmap()
        return count


class CaptureHelper():

    def __init__(self, width, height):
        self.capture = trinity.Tr2RenderTarget(width, height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)

    def SaveSurfaceToFile(self, filename):
        trinity.SaveRenderTarget(filename, self.capture)
        LogInfo('Saved to', filename)

    def CreateRenderSteps(self, rj, blitfx):
        rj.PushRenderTarget(self.capture).name = 'Begin screenshot capture'
        rj.PushDepthStencil(None).name = '    push depth'
        rj.RenderEffect(blitfx).name = '    Blit to screenshot'
        rj.PopDepthStencil().name = '    pop depth'
        rj.PopRenderTarget().name = 'End screenshot capture'


class FullScreenBlitter():

    def __init__(self, width, height):
        self.effect = trinity.Tr2Effect()
        self.effect.effectFilePath = 'res:/graphics/effect/optix/shaders/gammaBlit.fx'
        if self.effect.effectResource is None:
            LogWarn('Failed to load effect 1')
            return
        self.highpassEffect = trinity.Tr2Effect()
        self.highpassEffect.effectFilePath = 'res:/graphics/effect/optix/shaders/highpassFilter.fx'
        if self.highpassEffect.effectResource is None:
            LogWarn('Failed to load effect 1')
            return
        self.gaussianHorizEffect = trinity.Tr2Effect()
        self.gaussianHorizEffect.effectFilePath = 'res:/graphics/effect/optix/shaders/gaussianBlur.fx'
        if self.gaussianHorizEffect.effectResource is None:
            LogWarn('Failed to load effect 3')
            return
        self.gaussianVertEffect = trinity.Tr2Effect()
        self.gaussianVertEffect.effectFilePath = 'res:/graphics/effect/optix/shaders/gaussianBlur.fx'
        if self.gaussianVertEffect.effectResource is None:
            LogWarn('Failed to load effect 3')
            return
        for effect in [self.effect,
         self.highpassEffect,
         self.gaussianHorizEffect,
         self.gaussianVertEffect]:
            while effect.effectResource.isLoading:
                PD.Yield()

        self.blitcolor = trinity.Tr2Vector4Parameter()
        self.blitcolor.name = 'Color'
        for effect in [self.effect,
         self.highpassEffect,
         self.gaussianHorizEffect,
         self.gaussianVertEffect]:
            effect.PopulateParameters()
            effect.RebuildCachedData()
            effect.parameters.append(self.blitcolor)

        sizesParam = trinity.Tr2Vector4Parameter()
        sizesParam.name = 'InvSize'
        sizesParam.value = (1.0 / width,
         1.0 / height,
         0,
         0)
        for effect in [self.effect, self.highpassEffect]:
            effect.parameters.append(sizesParam)

        sizesHorizParam = trinity.Tr2Vector4Parameter()
        sizesHorizParam.name = 'invTexelSize'
        sizesHorizParam.value = (1.0 / width,
         0.0,
         0,
         0)
        self.gaussianHorizEffect.parameters.append(sizesHorizParam)
        sizesVertParam = trinity.Tr2Vector4Parameter()
        sizesVertParam.name = 'invTexelSize'
        sizesVertParam.value = (0.0,
         1.0 / height,
         0,
         0)
        self.gaussianVertEffect.parameters.append(sizesVertParam)

    def SetTexture(self, optixOutputTexture, highpassTexture, filteredTexture):
        tex = trinity.TriTexture2DParameter()
        tex.name = 'Texture'
        tex.SetResource(optixOutputTexture)
        for effect in [self.effect, self.highpassEffect]:
            effect.resources.append(tex)

        tex = trinity.TriTexture2DParameter()
        tex.name = 'Texture'
        tex.SetResource(highpassTexture)
        self.gaussianHorizEffect.resources.append(tex)
        tex = trinity.TriTexture2DParameter()
        tex.name = 'Texture'
        tex.SetResource(filteredTexture)
        self.gaussianVertEffect.resources.append(tex)
        tex = trinity.TriTexture2DParameter()
        tex.name = 'BloomTexture'
        tex.SetResource(highpassTexture)
        self.effect.resources.append(tex)

    def UpdateFrameCount(self, framecount):
        invFC = 1.0 / framecount if framecount > 0 else 1.0
        self.blitcolor.value = (invFC,
         invFC,
         invFC,
         invFC)


class FullOptixRenderer():
    __guid__ = 'paperDoll.FullOptixRenderer'
    instance = None

    def AddCallback(self, func, name, rj):
        cb = trinity.TriStepPythonCB()
        weakSelf = weakref.ref(self)
        cb.SetCallback(lambda : SkinRaytracingTools.FuncWrapper(weakSelf, func))
        cb.name = name
        rj.steps.append(cb)

    def GetFrameCount(self):
        return self.framecount

    def SaveScreenshot(self, filename):
        self.capture.SaveSurfaceToFile(filename)

    def AddRenderPreviewStep(self, renderJob):
        renderJob.SetStdRndStates(trinity.RM_FULLSCREEN).name = '    [optix] fullscreen quad'
        renderJob.PushDepthStencil(None).name = '    [optix] push depth'
        renderJob.RenderEffect(self.blitfx.effect).name = '    [optix] Blit to screenshot'
        renderJob.PopDepthStencil().name = '    [optix] pop depth'

    def RefreshMatrices(self):
        model = self.skinnedObject
        self.optix.RefreshMatrices(model, self.skinnedOptix)
        self.RunSkinningAndTesselation()
        self.ApplySettings()
        print 'Refreshed'

    @staticmethod
    def RaytraceFrame(selfRef):
        start = time.time()
        VP = SkinRaytracingTools.SetOptixMatrixFromTrinity(selfRef.optix, 'clipToWorld', selfRef.width / float(selfRef.height))
        if not SkinRaytracingTools.matEqual(VP, selfRef.previousVP):
            selfRef.previousVP = VP
            selfRef.outputBuffer.Clear()
            selfRef.framecount = 0
            model = selfRef.skinnedObject
            pos1 = model.GetBonePosition(model.GetBoneIndex('fj_eyeballLeft'))
            pos2 = model.GetBonePosition(model.GetBoneIndex('fj_eyeballRight'))
            dist1 = geo2.Vec3Distance(pos1, trinity.GetViewPosition())
            dist2 = geo2.Vec3Distance(pos2, trinity.GetViewPosition())
            autodof = min(dist1, dist2)
            dof = selfRef.settings.get('lens_focal_distance', autodof)
            print 'Auto-depth-of-field is at', autodof, ', actual focal distance is', dof
            selfRef.optix.SetFloat3('depthOfField', dof - trinity.GetFrontClip(), selfRef.settings['lens_radius'], 0)
        else:
            selfRef.framecount += 1
        selfRef.optix.SetUInt('frameIteration', selfRef.framecount)
        selfRef.oit.ResetAllocationCount()
        selfRef.rayCounter.ResetCount()
        time1 = time.time()
        selfRef.optix.Run(0, selfRef.width, selfRef.height)
        time2 = time.time()
        sec = time2 - time1
        raycount = selfRef.rayCounter.GetCount()
        raysec = 0
        if sec > 0:
            raysec = raycount / float(sec)
        time3 = time.time()
        if selfRef.framecount % 32 == 0:
            stop = time.time()
            print selfRef.oit.GetAllocationCount(), 'oit allocations'
            selfRef.blitfx.UpdateFrameCount(selfRef.framecount)
            selfRef.outputBuffer.CopyToTexture(selfRef.outputTexture)
            print 'time %05.3f / %05.3f / %05.3f / %05.3f msec' % (float(time1 - start) * 1000,
             float(time2 - time1) * 1000,
             float(time3 - time2) * 1000,
             float(stop - time3) * 1000),
            print '%d rays in %05.3f ms / %10d Krays/sec / %d rays per pixel' % (raycount,
             sec * 1000,
             raysec / 1000,
             selfRef.framecount)

    @telemetry.ZONE_METHOD
    def OnBeforeOptixPositionsUV(self):
        PD.SkinLightmapRenderer.DoChangeEffect('oxPosWorldUVEffect', self.oxMeshes)
        if self.skinnedObject is not None and self.skinnedObject.visualModel is not None:
            self.savedMeshes = self.skinnedObject.visualModel.meshes[:]
        filteredMeshes = [ ref.object for ref in self.oxMeshes.iterkeys() if ref.object is not None ]
        PD.SkinLightmapRenderer.DoCopyMeshesToVisual(self.skinnedObject, filteredMeshes)
        self.scene.filterList.removeAt(-1)
        self.scene.filterList.append(self.skinnedObject)
        self.scene.useFilterList = True

    @telemetry.ZONE_METHOD
    def OnBeforeOptixNormalsUV(self):
        PD.SkinLightmapRenderer.DoChangeEffect('oxNormalWorldUVEffect', self.oxMeshes)

    def OnAfterOptix(self):
        PD.SkinLightmapRenderer.DoRestoreShaders(meshes=self.oxMeshes)
        PD.SkinLightmapRenderer.DoCopyMeshesToVisual(self.skinnedObject, self.savedMeshes)
        del self.savedMeshes
        self.scene.useFilterList = False
        self.scene.filterList.removeAt(-1)

    def _InitUVUnwrap(self):
        self.oxMeshes = {}
        self.scatterFX = set()
        self.unwrapSize = 1024
        posUV = PD.SkinLightmapRenderer.PreloadEffect(PD.SkinLightmapRenderer.OPTIX_POSWORLD_UV_EFFECT)
        normalUV = PD.SkinLightmapRenderer.PreloadEffect(PD.SkinLightmapRenderer.OPTIX_NORMALWORLD_UV_EFFECT)
        deriv = PD.SkinLightmapRenderer.PreloadEffect(PD.SkinLightmapRenderer.STRETCHMAP_RENDERER_EFFECT)
        self.oxDepth = trinity.Tr2DepthStencil(self.unwrapSize, self.unwrapSize, trinity.DEPTH_STENCIL_FORMAT.D24S8, 1, 0)
        for mesh in self.skinnedObject.visualModel.meshes:
            if PD.SkinLightmapRenderer.IsScattering(mesh):
                m = PD.SkinLightmapRenderer.Mesh()
                m.ExtractOrigEffect(mesh)
                m.CreateOptixEffects(includeStretchMap=True)
                PD.AddWeakBlue(self, 'oxMeshes', mesh, m)
                fx = PD.GetEffectsFromMesh(mesh)
                for f in fx:
                    self.scatterFX.add(f)

        self.oxWorldPosMapUV = PD.SkinLightmapRenderer.CreateRenderTarget(self.unwrapSize, self.unwrapSize, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT, useRT=True)
        self.oxWorldNormalMapUV = PD.SkinLightmapRenderer.CreateRenderTarget(self.unwrapSize, self.unwrapSize, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT, useRT=True)
        self.stretchMap = PD.SkinLightmapRenderer.CreateRenderTarget(self.unwrapSize / 2, self.unwrapSize / 2, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT, useRT=True)
        rj = trinity.CreateRenderJob('Optix UV Unwrap')
        rj.PushRenderTarget(self.oxWorldPosMapUV)
        rj.PushDepthStencil(self.oxDepth)
        rj.Clear((0, 0, 0, 0), 1.0)
        rj.SetStdRndStates(trinity.RM_FULLSCREEN)
        vp = trinity.TriViewport()
        vp.x = 0
        vp.y = 0
        vp.width = self.unwrapSize
        vp.height = self.unwrapSize
        rj.SetViewport(vp)
        PD.SkinLightmapRenderer.AddCallback(self, FullOptixRenderer.OnBeforeOptixPositionsUV, 'onBeforeOptixPositionsUV', rj)
        rj.RenderScene(self.scene).name = 'Optix WorldPos (UV space)'
        PD.SkinLightmapRenderer.AddCallback(self, lambda weakSelf: PD.SkinLightmapRenderer.DoChangeEffect('oxNormalWorldUVEffect', meshes=weakSelf.oxMeshes), '', rj)
        rj.SetRenderTarget(self.oxWorldNormalMapUV)
        rj.Clear((0, 0, 0, 0), 1.0)
        rj.RenderScene(self.scene).name = 'Optix Normals (UV space)'
        rj.SetRenderTarget(self.stretchMap)
        rj.Clear((0, 0, 0, 0), 1.0)
        vp2 = trinity.TriViewport()
        vp2.x = 0
        vp2.y = 0
        vp2.width = self.unwrapSize / 2
        vp2.height = self.unwrapSize / 2
        rj.SetViewport(vp2)
        PD.SkinLightmapRenderer.AddCallback(self, lambda weakSelf: PD.SkinLightmapRenderer.DoChangeEffect('stretchmapRenderEffect', meshes=weakSelf.oxMeshes), '', rj)
        rj.RenderScene(self.scene).name = 'Stretchmap'
        PD.SkinLightmapRenderer.AddCallback(self, FullOptixRenderer.OnAfterOptix, 'onAfterOptix', rj)
        rj.PopRenderTarget()
        rj.PopDepthStencil()
        rj.ScheduleOnce()
        rj.WaitForFinish()
        if False:
            PD.SkinLightmapRenderer.SaveTarget(self.oxWorldPosMapUV, 'c:/depot/oxworldposuv2.dds', isRT=True)
            PD.SkinLightmapRenderer.SaveTarget(self.oxWorldNormalMapUV, 'c:/depot/oxworldnormaluv2.dds', isRT=True)
            PD.SkinLightmapRenderer.SaveTarget(self.stretchMap, 'c:/depot/stretchmap2.dds', isRT=True)
            print '** MAPS SAVED **'

    def RunSkinningAndTesselation(self):
        print '*** Tesselation phase ***'
        batchTypes = self.skinnedOptix[0]
        optix = self.optix
        ptx = {}
        ptx[72] = self.path + 'eve_skinning_kernel72.ptx'
        ptx[64] = self.path + 'eve_skinning_kernel64.ptx'
        for bytes, ptxfile in ptx.iteritems():
            LogInfo('Processing ', bytes, 'bytes/vertex')
            skinningProgram = trinity.Tr2OptixProgram(ptxfile, 'kernel_no_tesselation')
            skinningProgramTesselate = trinity.Tr2OptixProgram(ptxfile, 'kernel_tesselation')
            optix.SetEntryPointCount(2)
            optix.SetRayGenerationProgram(0, skinningProgram)
            optix.SetRayGenerationProgram(1, skinningProgramTesselate)
            for batchType in range(len(batchTypes)):
                batches = batchTypes[batchType]
                out = []

                def needsTesselation(fx):
                    return 'skinnedavatarhair_detailed.fx' in fx.effectFilePath.lower()

                for batch in batches:
                    if 'furshell' in batch[1].effectFilePath.lower():
                        out.append(None)
                        continue
                    tesselate = needsTesselation(batch[1])
                    triangle_count = batch[6]
                    bytes_per_vertex = batch[8]
                    if bytes_per_vertex != bytes:
                        out.append(None)
                        continue
                    vertex_buffer_output = trinity.Tr2OptixBuffer()
                    vertex_buffer_output.CreateUserData(bytes_per_vertex, triangle_count * 3 * 4 if tesselate else triangle_count * 3, trinity.OPTIX_BUFFER_INPUT_OUTPUT, True)
                    out.append(vertex_buffer_output)

                for i, batch in enumerate(batches):
                    if 'furshell' in batch[1].effectFilePath.lower():
                        continue
                    triangle_count = batch[6]
                    tesselate = needsTesselation(batch[1])
                    bytes_per_vertex = batch[8]
                    if bytes_per_vertex != bytes:
                        continue
                    if tesselate:
                        LogInfo('Tesselating geometry ', batch, ' of type ', batchType)
                    else:
                        LogInfo('Skinning geometry ', batch, ' of type ', batchType)
                    optix.SetBuffer('vertex_buffer', batch[2])
                    optix.SetBuffer('index_buffer', batch[3])
                    optix.SetBuffer('vertex_buffer_output', out[i])
                    optix.SetUInt('first_index_index', batch[5])
                    optix.SetBuffer('matrix_buffer', batch[7])
                    program = int(tesselate)
                    optix.Run(program, triangle_count, 1)
                    batch[0].SetBuffer('vertex_buffer', out[i])
                    if tesselate:
                        batch[0].SetPrimitiveCount(triangle_count * 4)

        optix.SetRayGenerationProgram(0, self.raygen)
        optix.SetRayGenerationProgram(1, self.raygen)

    def RemoveBadGeometry(self, model):
        self.haveBeard = False
        self.beardFx = None
        for mesh in model.visualModel.meshes:
            for area in mesh.decalAreas:
                if PD.IsBeard(area):
                    self.haveBeard = True
                    self.beardFx = area.effect
                    area.debugIsHidden = True
                    break

        for mesh in model.visualModel.meshes:
            for area in mesh.transparentAreas:
                lname = area.name.lower()
                if lname.startswith('eyeshadow_'):
                    mesh.transparentAreas.removeAt(-1)
                    break

        if False:
            for mesh in model.visualModel.meshes:
                for area in mesh.opaqueAreas:
                    lname = area.name.lower()
                    if 'eye' not in lname or 'eyewet' in lname or 'eyelash' in lname:
                        mesh.opaqueAreas.removeAt(-1)
                        break

                for area in mesh.transparentAreas:
                    lname = area.name.lower()
                    if 'eye' not in lname or 'eyewet' in lname or 'eyelash' in lname:
                        mesh.transparentAreas.removeAt(-1)
                        break

        if False:
            print 'raytracing', len(model.visualModel.meshes), 'meshes'
            for mesh in model.visualModel.meshes:
                lname = mesh.name.lower()
                if not lname.startswith('hair'):
                    print 'removing', lname
                    mesh.opaqueAreas.removeAt(-1)
                    mesh.decalAreas.removeAt(-1)
                    mesh.transparentAreas.removeAt(-1)
                elif False:
                    print 'removing', lname
                    for a in mesh.opaqueAreas:
                        print 'opaque', a.name

                    for a in mesh.decalAreas:
                        print 'decal', a.name

                    for a in mesh.transparentAreas:
                        print 'transp', a.name

                    mesh.opaqueAreas.removeAt(-1)
                    mesh.decalAreas.removeAt(-1)
                    mesh.transparentAreas.removeAt(-1)
                else:
                    print 'keeping', lname

    def TransferBeardParameters(self, optix):
        if self.haveBeard:
            LogInfo('Beard found')
            beardLength = self.settings['beardLength']
            optix.SetFloat3('beardOptions', beardLength[0], beardLength[1], self.settings['beardGravity'])
            floatMap = {'FurLength': 'beard_fur_length',
             'UVScale': 'beard_uv_scale',
             'AlphaMultiplier': 'beard_alpha_multiplier',
             'CombStrength': 'beard_comb_strength',
             'FurGrainRotation': 'beard_fur_grain_rotation',
             'MirrorGrain': 'beard_mirror_grain',
             'FurParallax': 'beard_fur_parallax'}
            float3Map = {'gravityOffset': 'beard_gravity_offset',
             'MaterialDiffuseColor': 'beard_diffuse_color'}
            for param in self.beardFx.parameters:
                optixName = floatMap.get(param.name, None)
                if optixName is not None:
                    optix.SetFloat(optixName, param.value)
                else:
                    optixName = float3Map.get(param.name, None)
                    if optixName is not None:
                        optix.SetFloat3(optixName, param.value[0], param.value[1], param.value[2])

    def GenerateBeardGeometry(self, optix, path, any_hit_shadow):
        if not self.haveBeard:
            return None
        LogInfo('generating beard splines')
        SkinRaytracingTools.SetOptixMatrixFromTrinity(optix, 'clipToWorld')
        beardProgram = trinity.Tr2OptixProgram(path + 'eve_beard_kernel.ptx', 'kernel')
        curveOutputBuffer = trinity.Tr2OptixBuffer()
        curveCount = 512
        curveOutputBuffer.CreateUserData(80, curveCount * curveCount, trinity.OPTIX_BUFFER_INPUT_OUTPUT, True)
        optix.SetBuffer('output', curveOutputBuffer)
        rayTypeCount = optix.GetRayTypeCount()
        optix.SetRayTypeCount(1)
        optix.SetEntryPointCount(2)
        optix.SetRayGenerationProgram(0, beardProgram)
        optix.SetRayGenerationProgram(1, beardProgram)
        optix.SetEntryPointCount(1)
        LogInfo('beard: about to Run')
        optix.Run(0, curveCount, curveCount)
        LogInfo('beard: Run done')
        optix.SetRayTypeCount(rayTypeCount)
        hairGeometry = trinity.Tr2OptixGeometry()
        hairGeometry.InitializeFromProgram(path + 'bezier_curves.ptx', 'intersect', 'bounds')
        subdivideDepth = 2
        hairGeometry.SetPrimitiveCount(curveCount * curveCount * (1 << subdivideDepth))
        optix.SetUInt('presubdivide_depth', subdivideDepth)
        optix.SetBuffer('curves', curveOutputBuffer)
        LogInfo('beard: geometry setup done')
        beardInstance = trinity.Tr2OptixGeometryInstance()
        beardInstance.SetGeometry(hairGeometry)
        closest_hit_BeardShader = trinity.Tr2OptixProgram(path + 'eve_beard_shader.ptx', 'closest_hit_BeardShader')
        beardMaterial = trinity.Tr2OptixMaterial()
        beardMaterial.SetClosestHit(0, closest_hit_BeardShader)
        beardMaterial.SetAnyHit(1, any_hit_shadow)
        beardInstance.SetMaterial(beardMaterial)
        LogInfo('beard: geometry instance setup done')
        return beardInstance

    def _DoInit(self, scene = None):
        model = None
        if scene is None:
            scene = PD.SkinLightmapRenderer.Scene()
        self.scene = scene
        self.previousVP = trinity.TriMatrix()
        self.framecount = 1
        self.useOIT = True
        if scene is None:
            LogWarn('No scene!')
            return
        for dynamic in scene.dynamics:
            if dynamic.__typename__ == 'Tr2IntSkinnedObject':
                model = dynamic
                break
        else:
            LogWarn('No Tr2IntSkinnedObject found')
            return

        if model is None:
            LogWarn('No Tr2IntSkinnedObject found')
            return
        self.skinnedObject = model
        if self.skinnedObject.visualModel is None:
            LogWarn('skinnedObject has no visualMeshes')
            return
        bg = trinity.renderContext.GetDefaultBackBuffer()
        step = trinity.renderJobs.FindStepByName('SET_SWAPCHAIN_RT')
        if step is not None:
            bg = step.renderTarget
        self.width = self.settings.get('outputWidth', bg.width)
        self.height = self.settings.get('outputHeight', bg.height)
        self.blitfx = FullScreenBlitter(self.width, self.height)
        self.RemoveBadGeometry(model)
        outputTexture = trinity.TriTextureRes(self.width, self.height, 1, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT)
        self.outputTexture = outputTexture
        self.capture = CaptureHelper(self.width, self.height)
        self._InitUVUnwrap()
        for steps in trinity.renderJobs.recurring:
            if steps.name == 'FullOptixRenderer':
                steps.UnscheduleRecurring()

        start = time.clock()
        optix = trinity.Tr2Optix()
        self.optix = optix
        optix.SetInteropDevice()
        optix.SetRayTypeCount(4)
        optix.SetEntryPointCount(1)
        if False:
            optix.EnableAllExceptions()
            optix.SetPrintEnabled(True)
            optix.SetPrintBufferSize(16384)
        optix.SetUInt('radiance_ray_type', 0)
        optix.SetUInt('shadow_ray_type', 1)
        optix.SetUInt('translucency_ray_type', 2)
        optix.SetUInt('translucency_ray_type', 3)
        optix.SetFloat('scene_epsilon', 0.001)
        optix.SetUInt('frameIteration', 0)
        self.outputBuffer = trinity.Tr2OptixBuffer()
        self.outputBuffer.CreateFloat4(self.width, self.height, trinity.OPTIX_BUFFER_INPUT_OUTPUT)
        optix.SetBuffer('output_buffer', self.outputBuffer)
        self.ApplySettings()
        path = str(blue.paths.ResolvePath('res:/graphics/effect/optix/NCC/'))
        self.path = path
        LogInfo('Getting files from', path)
        everything = []
        any_hit_shadow = trinity.Tr2OptixProgram(path + 'eve_shadow.ptx', 'any_hit_shadow')
        any_hit_shadow_blend = trinity.Tr2OptixProgram(path + 'eve_shadow.ptx', 'any_hit_shadow_blend')
        shader_diffuse_only_feeler = trinity.Tr2OptixProgram(path + 'eve_bounce.ptx', 'closest_hit_DiffuseOnlyFeeler2')
        any_hit_cutout = trinity.Tr2OptixProgram(path + 'eve_cutout.ptx', 'any_hit_CutoutMask')
        any_hit_diffuse_feeler_blend = trinity.Tr2OptixProgram(path + 'eve_shadow.ptx', 'any_hit_diffuse_feeler_blend')
        everything.append(any_hit_shadow)
        everything.append(any_hit_shadow_blend)
        everything.append(shader_diffuse_only_feeler)
        everything.append(any_hit_cutout)
        mainRay = 0
        shadowRay = 1
        bounceRay = 3

        def MakeMaterialWithShader(shader):
            material = trinity.Tr2OptixMaterial()
            material.SetClosestHit(mainRay, shader)
            material.SetAnyHit(shadowRay, any_hit_shadow)
            material.SetClosestHit(bounceRay, shader_diffuse_only_feeler)
            everything.append(material)
            return (material, shader)

        def MakeMaterial(ptxFile, shaderName):
            shader = trinity.Tr2OptixProgram(path + ptxFile + '.ptx', shaderName)
            everything.append(shader)
            return MakeMaterialWithShader(shader)

        def MakeDecal(material):
            material.SetAnyHit(mainRay, any_hit_cutout)
            material.SetAnyHit(shadowRay, any_hit_shadow_blend)
            material.SetAnyHit(bounceRay, any_hit_cutout)

        skin_single_material, skin_single_shade = MakeMaterial('eve_skin', 'closest_hit_ShadeSinglePassSkin_Single2')
        skin_single_material_scatter = MakeMaterial('eve_skin', 'closest_hit_ShadeSinglePassSkin_Single_Scatter2')[0]
        skin_single_material_decal = MakeMaterialWithShader(skin_single_shade)[0]
        MakeDecal(skin_single_material_decal)
        glasses_shade = trinity.Tr2OptixProgram(path + 'eve_glasses.ptx', 'glasses_shade')
        glasses_shadow = trinity.Tr2OptixProgram(path + 'eve_glasses.ptx', 'glasses_shadow')
        glass_material = trinity.Tr2OptixMaterial()
        glass_material.SetAnyHit(mainRay, glasses_shade)
        glass_material.SetAnyHit(shadowRay, glasses_shadow)
        glass_material.SetClosestHit(bounceRay, shader_diffuse_only_feeler)
        everything.append(glasses_shade)
        everything.append(glasses_shadow)
        vizNames = ['closest_hit_VizNormal',
         'closest_hit_VizUV',
         'closest_hit_VizConstantColor',
         'closest_hit_VizDiffuse']
        vizualizer, vizualizer_shade = MakeMaterial('eve_basic', vizNames[0])
        vizualizer_decal = MakeMaterialWithShader(vizualizer_shade)[0]
        MakeDecal(vizualizer_decal)
        skin_double_material, skin_double_shade = MakeMaterial('eve_skin', 'closest_hit_ShadeSinglePassSkin_Double2')
        skin_double_material_decal = MakeMaterialWithShader(skin_double_shade)[0]
        MakeDecal(skin_double_material_decal)
        skin_double_material_transparent = MakeMaterial('eve_skin', 'closest_hit_ShadeSinglePassSkin_Double2_Blend')[0]
        skin_double_material_transparent.SetAnyHit(mainRay, any_hit_cutout)
        skin_double_material_transparent.SetAnyHit(shadowRay, any_hit_shadow_blend)
        skin_double_material_transparent.SetAnyHit(bounceRay, any_hit_cutout)
        avatar_brdf_material, avatar_brdf_shade = MakeMaterial('eve_brdf', 'closest_hit_ShadeAvatarBRDF_Single2')
        avatar_brdf_material_decal = MakeMaterialWithShader(avatar_brdf_shade)[0]
        MakeDecal(avatar_brdf_material_decal)
        avatar_brdf_double_material, avatar_brdf_double_shade = MakeMaterial('eve_brdf', 'closest_hit_ShadeAvatarBRDF_Double2')
        avatar_brdf_double_material_decal = MakeMaterialWithShader(avatar_brdf_double_shade)[0]
        MakeDecal(avatar_brdf_double_material_decal)
        avatar_hair_material = trinity.Tr2OptixMaterial()
        avatar_hair_shade = trinity.Tr2OptixProgram(path + 'eve_hair.ptx', 'closest_hit_ShadeAvatarHair2' if self.useOIT else 'closest_hit_ShadeAvatarHair2_Blend')
        avatar_hair_material.SetClosestHit(mainRay, avatar_hair_shade)
        if self.useOIT:
            avatar_hair_oit = trinity.Tr2OptixProgram(path + 'eve_hair.ptx', 'any_hit_HairOIT')
            avatar_hair_material.SetAnyHit(mainRay, avatar_hair_oit)
        avatar_hair_material.SetAnyHit(shadowRay, any_hit_shadow_blend)
        avatar_hair_material.SetClosestHit(bounceRay, shader_diffuse_only_feeler)
        everything.append(avatar_hair_shade)
        everything.append(avatar_hair_material)
        avatar_hair_material_decal = trinity.Tr2OptixMaterial()
        avatar_hair_material_decal.SetClosestHit(mainRay, avatar_hair_shade)
        avatar_hair_material_decal.SetAnyHit(mainRay, avatar_hair_oit if self.useOIT else any_hit_cutout)
        avatar_hair_material_decal.SetAnyHit(shadowRay, any_hit_shadow_blend)
        avatar_hair_material_decal.SetClosestHit(bounceRay, shader_diffuse_only_feeler)
        avatar_hair_material_decal.SetAnyHit(bounceRay, any_hit_cutout)
        everything.append(avatar_hair_material_decal)
        eye_shade = trinity.Tr2OptixProgram(path + 'eve_eyes.ptx', 'closest_hit_ShadeEye')
        eye_material = trinity.Tr2OptixMaterial()
        eye_material.SetClosestHit(mainRay, eye_shade)
        eye_material.SetAnyHit(shadowRay, any_hit_shadow)
        everything.append(eye_shade)
        everything.append(eye_material)
        eye_wetness_shade = trinity.Tr2OptixProgram(path + 'eve_eyes.ptx', 'closest_hit_ShadeEyeWetness')
        eye_wetness_material = trinity.Tr2OptixMaterial()
        eye_wetness_material.SetClosestHit(mainRay, eye_wetness_shade)
        eye_wetness_material.SetAnyHit(shadowRay, any_hit_shadow)
        everything.append(eye_wetness_shade)
        everything.append(eye_wetness_material)
        portrait_basic_material, portrait_basic_shade = MakeMaterial('eve_basic', 'closest_hit_ShadePortraitBasic')
        portrait_basic_material_decal = MakeMaterialWithShader(portrait_basic_shade)[0]
        MakeDecal(portrait_basic_material_decal)
        LogInfo('global setup OK', time.clock() - start, 'seconds')

        def MakeSamplerFromMap(texture, name):
            sampler = trinity.Tr2OptixTextureSampler()
            sampler.CreateFromSurface(texture)
            sampler.SetNormalizedIndexingMode(True)
            optix.SetSampler(name, sampler)
            LogInfo('No-Copy Interop for ', name)
            everything.append(sampler)

        MakeSamplerFromMap(self.oxWorldPosMapUV, 'world_pos_uv_buffer')
        MakeSamplerFromMap(self.oxWorldNormalMapUV, 'world_normal_uv_buffer')
        MakeSamplerFromMap(self.stretchMap, 'stretchmap_buffer')
        useHdrProbe = False
        if useHdrProbe:
            optix.SetSamplerFromProbe('hdr_probe_sampler', 'c:/depot/optix/data/Japan_subway2_FINAL.hdr')
        start = time.clock()
        self.skinnedOptix = optix.CreateFromSkinnedModel(model, 72, path + 'triangle72.ptx', 'mesh_intersect', 'mesh_bounds', 64, path + 'triangle64.ptx', 'mesh_intersect', 'mesh_bounds')
        optixBatches = self.skinnedOptix[0]
        self.TransferBeardParameters(optix)
        group = trinity.Tr2OptixGeometryGroup()
        groupChildren = []
        self.rayCounter = RayCountHelper(self.optix)
        self.oit = OitHelper(self.optix)
        self.raygen = trinity.Tr2OptixProgram(path + 'raygen.ptx', 'ray_request')
        self.RunSkinningAndTesselation()
        start = time.clock()
        samplers = SkinRaytracingTools.InteropAllTextures(optix, model, waitForFinish=True)
        everything.append(samplers)
        backdrop = trinity.TriTexture2DParameter()
        backdrop.resourcePath = self.settings['backgroundBitmap']
        skinmap = trinity.TriTexture2DParameter()
        skinmap.resourcePath = 'res:/Graphics/Character/female/paperdoll/head/head_generic/SkinMap.png'
        blue.resMan.Wait()
        everything.append(SkinRaytracingTools.InteropTexture('BackgroundEnvMap', backdrop.resource, waitForFinish=True, scope=optix))
        everything.append(SkinRaytracingTools.InteropTexture('SkinMap', skinmap.resource, waitForFinish=True, scope=optix))
        LogInfo('texture interop OK', time.clock() - start, 'seconds')
        splines = self.GenerateBeardGeometry(optix, path, any_hit_shadow)
        if splines is not None:
            groupChildren.append(splines)
        print '*** Raytracing phase ***'

        def SetAlphaRef(instance, batchType):
            if batchType == 1:
                instance.SetFloat4('alphaRef', 0.75, 0, 0, 0)
            elif batchType == 2:
                instance.SetFloat4('alphaRef', 0.01, 0, 0, 0)

        haveGlasses = False
        for batchType in range(len(optixBatches)):
            isOpaque = batchType == 0
            batches = optixBatches[batchType]
            for batch in batches:
                if 'furshell' in batch[1].effectFilePath.lower():
                    continue
                instance = trinity.Tr2OptixGeometryInstance()
                everything.append(instance)
                instance.SetGeometry(batch[0])
                r = random.random()
                g = random.random()
                b = random.random()
                instance.SetFloat4('viz_constant_color', r, g, b, 1.0)
                fxpath = batch[1].effectFilePath.lower()
                if False:
                    instance.SetMaterial(vizualizer if isOpaque else vizualizer_decal)
                elif 'glassshader' in fxpath:
                    instance.SetMaterial(glass_material)
                    if not haveGlasses:
                        haveGlasses = True
                elif 'skinnedavatarbrdfsinglepassskin_single.fx' in fxpath:
                    if batch[1] in self.scatterFX:
                        instance.SetMaterial(skin_single_material_scatter)
                    else:
                        instance.SetMaterial(skin_single_material if isOpaque else skin_single_material_decal)
                    SetAlphaRef(instance, batchType)
                elif 'skinnedavatarbrdfsinglepassskin_double.fx' in fxpath:
                    instance.SetMaterial([skin_double_material, skin_double_material_decal, skin_double_material_transparent][batchType])
                    SetAlphaRef(instance, batchType)
                elif 'skinnedavatarbrdflinear.fx' in fxpath:
                    instance.SetMaterial(avatar_brdf_material if isOpaque else avatar_brdf_material_decal)
                elif 'skinnedavatarbrdfdoublelinear.fx' in fxpath:
                    instance.SetMaterial(avatar_brdf_double_material if isOpaque else avatar_brdf_double_material_decal)
                elif 'skinnedavatarhair_detailed.fx' in fxpath:
                    instance.SetMaterial(avatar_hair_material if isOpaque else avatar_hair_material_decal)
                    instance.SetFloat4('alphaRef', 0.01, 0, 0, 0)
                    instance.SetUInt('enableCulling', 0)
                elif 'eyeshader.fx' in fxpath:
                    instance.SetMaterial(eye_material)
                elif 'eyewetnessshader.fx' in fxpath:
                    instance.SetMaterial(eye_wetness_material)
                elif 'portraitbasic.fx' in fxpath:
                    instance.SetMaterial(portrait_basic_material if isOpaque else portrait_basic_material_decal)
                else:
                    instance.SetMaterial(vizualizer if isOpaque else vizualizer_decal)
                SkinRaytracingTools.CopyParametersToContext(batch[1], instance)
                groupChildren.append(instance)

        group.SetChildCount(len(groupChildren))
        for x in xrange(len(groupChildren)):
            group.SetChild(x, groupChildren[x])

        everything.append(group)
        group.SetAcceleration('Bvh', 'Bvh')
        LogInfo('scene interop OK', time.clock() - start, 'seconds')
        start = time.clock()
        bufEveLights = SkinRaytracingTools.CreateBufferForLights(scene.lights, useHdrProbe)
        optix.SetBuffer('trinity_lights', bufEveLights)
        LogInfo('lights interop OK', time.clock() - start, 'seconds')
        start = time.clock()
        optix.SetGeometryGroup('top_scene', group)
        optix.SetGeometryGroup('shadow_casters', group)
        optix.SetRayGenerationProgram(0, self.raygen)
        optix.SetEntryPointCount(1)
        miss = None
        if not useHdrProbe:
            miss = trinity.Tr2OptixProgram(path + 'eve_miss.ptx', 'miss')
        else:
            miss = trinity.Tr2OptixProgram(path + 'eve_miss_probe.ptx', 'miss')
        optix.SetMissProgram(3, miss)
        optix.SetFloat3('bg_color', 1.0, 0, 0)
        everything.append(miss)
        if False:
            exception = trinity.Tr2OptixProgram(path + 'eve_miss.ptx', 'exception')
            optix.SetExceptionProgram(0, exception)
            everything.append(exception)
        optix.SetStackSize(4096)
        self.everything = everything
        SkinRaytracingTools.SetOptixMatrixFromTrinity(optix, 'clipToWorld', self.width / float(self.height))
        LogInfo('general setup OK', time.clock() - start, 'seconds')
        optix.ReportObjectCounts()
        start = time.clock()
        optix.Compile()
        LogInfo('compile OK', time.clock() - start, 'seconds')
        start = time.clock()
        optix.Validate()
        LogInfo('validate OK', time.clock() - start, 'seconds')
        start = time.clock()
        optix.Run(0, 0, 0)
        LogInfo('BVH OK', time.clock() - start, 'seconds')
        start = time.clock()
        self.blitfx.SetTexture(outputTexture, outputTexture, outputTexture)
        rj = trinity.CreateRenderJob('FullOptixRenderer')
        rj.PushRenderTarget(self.outputRT)
        rj.PushDepthStencil(None)
        self.AddCallback(FullOptixRenderer.RaytraceFrame, 'Raytrace Frame', rj)
        rj.CopyRtToTexture(outputTexture).name = 'cuda -> outputTexture'
        rj.PopDepthStencil()
        rj.PopRenderTarget()
        rj.SetStdRndStates(trinity.RM_FULLSCREEN).name = 'fullscreen quad'
        rj.RenderEffect(self.blitfx.effect).name = '           blit'
        self.capture.CreateRenderSteps(rj, self.blitfx.effect)
        rj.steps.append(trinity.TriStepRenderFps())
        rj.ScheduleRecurring(insertFront=False)
        self.renderJob = rj
        LogInfo('final setup OK', time.clock() - start, 'seconds')
        model.display = False
        self.EnablePaperDollJobs(False)

    @staticmethod
    def EnablePaperDollJobs(enable):
        if False:
            for job in trinity.renderJobs.recurring:
                if 'paperdollrenderjob' in job.name.lower():
                    for step in job.steps:
                        step.enabled = enable

        if enable:
            trinity.device.tickInterval = 10
        else:
            trinity.device.tickInterval = 0

    def ApplySettings(self):
        self.optix.SetFloat('light_size', self.settings['light_size'])
        self.optix.SetFloat3('depthOfField', 1.0, self.settings['lens_radius'], 0)
        self.optix.SetFloat('HairShadows', self.settings['HairShadows'])
        self.optix.SetFloat('EnvMapBoost', self.settings['EnvMapBoost'] / 3.1415927)
        self.previousVP.Identity()

    def SetLensRadius(self, lens_radius):
        self.settings['lens_radius'] = lens_radius
        self.ApplySettings()

    def SetLensFocalDistance(self, lens_focal_distance):
        if lens_focal_distance <= 0:
            self.settings.pop('lens_focal_distance', 0)
        else:
            self.settings['lens_focal_distance'] = lens_focal_distance
        self.ApplySettings()

    def SetLightSize(self, light_size):
        self.settings['light_size'] = light_size
        self.ApplySettings()

    def SetHairShadowsEnabled(self, enabled):
        self.settings['HairShadows'] = float(enabled)
        self.ApplySettings()

    def SetBackgroundIntensity(self, intensity):
        self.settings['EnvMapBoost'] = intensity
        self.ApplySettings()

    def __init__(self, scene = None, backgroundBitmap = None, memento = None, beardLength = (0.01, 0.01), beardGravity = 0.0005, outputWidth = None, outputHeight = None, asyncSetup = True, listenForUpdate = True):
        LogInfo('init', self)
        blue.motherLode.maxMemUsage = 0
        blue.resMan.ClearAllCachedObjects()
        self.framecount = 0
        self.listenForUpdate = listenForUpdate
        if memento is not None:
            self.settings = memento
        else:
            self.settings = {}
            self.settings['light_size'] = 0.125
            self.settings['lens_radius'] = 0.001
            self.settings['HairShadows'] = 1.0
            self.settings['EnvMapBoost'] = 1.0
            self.settings['backgroundBitmap'] = backgroundBitmap if backgroundBitmap is not None else 'res:/texture/global/red_blue_ramp.dds'
            self.settings['beardLength'] = beardLength
            self.settings['beardGravity'] = beardGravity
            if outputWidth is not None:
                self.settings['outputWidth'] = outputWidth
            if outputHeight is not None:
                self.settings['outputHeight'] = outputHeight
        if asyncSetup:
            uthread.new(self._DoInit, scene=scene)
        else:
            self._DoInit(scene=scene)

    def GetMemento(self):
        return self.settings

    def __del__(self):
        LogInfo('deleting', self)
        if hasattr(self, 'renderJob'):
            self.renderJob.UnscheduleRecurring()
            self.renderJob = None
        del self.raygen
        del self.rayCounter
        del self.oit
        del self.outputBuffer
        del self.skinnedOptix
        del self.everything
        LogInfo('Post-cleanup leak check:')
        self.optix.ReportObjectCounts()
        self.EnablePaperDollJobs(True)

    @staticmethod
    def Pause():
        if FullOptixRenderer.instance is not None:
            FullOptixRenderer.instance.renderJob.UnscheduleRecurring()

    @staticmethod
    def NotifyUpdate():
        if FullOptixRenderer.instance is not None and FullOptixRenderer.instance.listenForUpdate:
            LogInfo('NotifyUpdate, restarting', FullOptixRenderer.instance)
            memento = FullOptixRenderer.instance.GetMemento()
            FullOptixRenderer.instance = None
            FullOptixRenderer.instance = FullOptixRenderer(memento=memento)


class ShipOptixRenderer():
    __guid__ = 'paperDoll.ShipOptixRenderer'
    instance = None

    def AddCallback(self, func, name, rj):
        cb = trinity.TriStepPythonCB()
        weakSelf = weakref.ref(self)
        cb.SetCallback(lambda : SkinRaytracingTools.FuncWrapper(weakSelf, func))
        cb.name = name
        rj.steps.append(cb)

    def GetFrameCount(self):
        return self.framecount

    def SaveScreenshot(self, filename):
        self.capture.SaveSurfaceToFile(filename)

    def AddRenderPreviewStep(self, renderJob):
        renderJob.SetStdRndStates(trinity.RM_FULLSCREEN).name = '    [optix] fullscreen quad'
        renderJob.PushDepthStencil(None).name = '    [optix] push depth'
        renderJob.RenderEffect(self.blitfx.effect).name = '    [optix] Blit to screenshot'
        renderJob.PopDepthStencil().name = '    [optix] pop depth'

    @staticmethod
    def RaytraceFrame(selfRef):
        start = time.time()
        VP = SkinRaytracingTools.SetOptixMatrixFromTrinity(selfRef.optix, 'clipToWorld', selfRef.width / float(selfRef.height))
        if not SkinRaytracingTools.matEqual(VP, selfRef.previousVP):
            selfRef.previousVP = VP
            selfRef.outputBuffer.Clear()
            selfRef.framecount = 0
            pos1 = (0, 0, 0)
            pos2 = pos1
            dist1 = geo2.Vec3Distance(pos1, trinity.GetViewPosition())
            dist2 = geo2.Vec3Distance(pos2, trinity.GetViewPosition())
            autodof = min(dist1, dist2)
            dof = selfRef.settings.get('lens_focal_distance', autodof)
            LogInfo('Auto-depth-of-field is at', autodof, ', actual focal distance is', dof)
            selfRef.optix.SetFloat3('depthOfField', dof - trinity.GetFrontClip(), selfRef.settings['lens_radius'], 0)
        else:
            selfRef.framecount += 1
        selfRef.optix.SetUInt('frameIteration', selfRef.framecount)
        selfRef.oit.ResetAllocationCount()
        selfRef.rayCounter.ResetCount()
        time1 = time.time()
        selfRef.optix.Run(0, selfRef.width, selfRef.height)
        time2 = time.time()
        traceTime = time2 - time1
        raycount = selfRef.rayCounter.GetCount()
        raysec = 0
        if traceTime > 0:
            raysec = raycount / float(traceTime)
        time3 = time.time()
        if selfRef.framecount % 32 == 0:
            oit = selfRef.oit.GetAllocationCount()
            if oit > 0:
                print oit, 'oit allocations'
            selfRef.blitfx.UpdateFrameCount(selfRef.framecount)
            selfRef.outputBuffer.CopyToTexture(selfRef.outputTexture)
            stop = time.time()
            message = 'time: call %05.3f / trace %05.3f / read %05.3f ms' % (float(time1 - start) * 1000, float(time2 - time1) * 1000, float(stop - time3) * 1000)
            message += '// traced %d rays in %05.3f ms / %10d Krays/sec / %d frames' % (raycount,
             traceTime * 1000,
             raysec / 1000,
             selfRef.framecount)
            LogInfo(message)

    def ConvertCubeMapToSH(self, optix, ptxPath, cubeResPath):
        self.shBuffer = trinity.Tr2OptixBuffer()
        self.shBuffer.CreateFloat4(9, 1, trinity.OPTIX_BUFFER_INPUT_OUTPUT)
        optix.SetBuffer('sh_buffer', self.shBuffer)
        self.shBuffer.Clear()
        program = trinity.Tr2OptixProgram(ptxPath + 'cubemapsh.ptx', 'kernel')
        optix.SetRayGenerationProgram(0, program)
        optix.ReportObjectCounts()
        cube = trinity.TriTextureCubeParameter()
        cube.resourcePath = cubeResPath
        cube.name = 'Nebula'
        blue.resMan.Wait()
        mipmaps, names = SkinRaytracingTools.ConvertCubeToTextures(cube)
        for i in range(len(names)):
            if i < len(mipmaps):
                sampler = trinity.Tr2OptixTextureSampler()
                sampler.CreateFromTexture(mipmaps[i])
                sampler.SetNormalizedIndexingMode(True)
                optix.SetSampler(cube.name + names[i], sampler)
                LogInfo('No-Copy Cube Side Interop for ' + cube.name + names[i])

        optix.Run(0, cube.resource.width, cube.resource.width)
        if False:
            names = ['Y00',
             'Y1m1',
             'Y10',
             'Y11',
             'Y2m2',
             'Y2m1',
             'Y20',
             'Y21',
             'Y22']
            self.shBuffer.Map()
            ofs = 0
            for name in names:
                print name, ': (',
                print self.shBuffer.GetUserDataF(ofs), ',',
                ofs = ofs + 4
                print self.shBuffer.GetUserDataF(ofs), ',',
                ofs = ofs + 4
                print self.shBuffer.GetUserDataF(ofs), ')'
                ofs = ofs + 4

            self.shBuffer.Unmap()

    def CachedCreateMaterial(self, path, effect):
        material = self.materialCache.get(effect, None)
        if material is not None:
            return material
        shader = None
        if effect in ('tripleglowv3', 'doubleglowv3', 'singleglowv3'):
            shader = trinity.Tr2OptixProgram(path + 'v3ship_glow.ptx', 'closest_hit_' + effect)
        elif effect in ('singleheatv3',):
            shader = trinity.Tr2OptixProgram(path + 'v3ship_heat.ptx', 'closest_hit_' + effect)
        elif effect in ('tripleglowoilv3',):
            shader = trinity.Tr2OptixProgram(path + 'v3ship_glow_oil.ptx', 'closest_hit_' + effect)
        elif effect == 'skinned_tripleglowv3':
            shader = trinity.Tr2OptixProgram(path + 'v3ship_glow.ptx', 'closest_hit_tripleglowv3')
        if shader is None:
            return
        material = trinity.Tr2OptixMaterial()
        material.SetClosestHit(0, shader)
        material.SetAnyHit(1, self.any_hit_shadow)
        return material

    def _DoInit(self, scene = None):
        if scene is None:
            scene = trinity.device.scene
        self.scene = scene
        self.previousVP = trinity.TriMatrix()
        self.framecount = 1
        self.materialCache = {}
        self.useOIT = True
        if scene is None:
            LogWarn('No scene!')
            return
        bg = trinity.renderContext.GetDefaultBackBuffer()
        step = trinity.renderJobs.FindStepByName('SET_SWAPCHAIN_RT')
        if step is not None:
            bg = step.renderTarget
        self.width = self.settings.get('outputWidth', bg.width)
        self.height = self.settings.get('outputHeight', bg.height)
        self.blitfx = FullScreenBlitter(self.width, self.height)
        bloomScale = 4
        if False:
            self.highpassRT = PD.SkinLightmapRenderer.CreateRenderTarget(self.width / bloomScale, self.height / bloomScale, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT)
            self.filteredRT = PD.SkinLightmapRenderer.CreateRenderTarget(self.width / bloomScale, self.height / bloomScale, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT)
        outputTexture = trinity.TriTextureRes(self.width, self.height, 1, trinity.PIXEL_FORMAT.R32G32B32A32_FLOAT)
        self.outputTexture = outputTexture
        self.capture = CaptureHelper(self.width, self.height)
        for steps in trinity.renderJobs.recurring:
            if steps.name == 'ShipOptixRenderer':
                steps.UnscheduleRecurring()

        path = str(blue.paths.ResolvePath('res:/graphics/effect/optix/ship/'))
        self.path = path
        LogInfo('Getting files from', path)
        start = time.clock()
        optix = trinity.Tr2Optix()
        self.optix = optix
        optix.SetInteropDevice()
        optix.SetRayTypeCount(4)
        optix.SetEntryPointCount(1)
        if False:
            optix.EnableAllExceptions()
        if False:
            optix.SetPrintEnabled(True)
            optix.SetPrintBufferSize(16384)
        optix.SetFloat('scene_epsilon', 0.01)
        optix.SetUInt('frameIteration', 0)
        nebula = PD.FindResourceByName(scene.backgroundEffect, 'NebulaMap') if scene.backgroundEffect is not None else None
        if nebula is not None:
            LogInfo('Converting to SH ', nebula.resourcePath)
            self.ConvertCubeMapToSH(optix, path, nebula.resourcePath)
        else:
            self.shBuffer = trinity.Tr2OptixBuffer()
            self.shBuffer.CreateFloat4(9, 1, trinity.OPTIX_BUFFER_INPUT_OUTPUT)
            optix.SetBuffer('sh_buffer', self.shBuffer)
            self.shBuffer.Clear()
        self.outputBuffer = trinity.Tr2OptixBuffer()
        self.outputBuffer.CreateFloat4(self.width, self.height, trinity.OPTIX_BUFFER_INPUT_OUTPUT)
        optix.SetBuffer('output_buffer', self.outputBuffer)
        self.ApplySettings()
        everything = []
        mainRay = 0
        shadowRay = 1
        bounceRay = 3

        def MakeMaterialWithShader(shader):
            return (material, shader)

        def MakeMaterial(ptxFile, shaderName):
            everything.append(shader)
            return MakeMaterialWithShader(shader)

        LogInfo('global setup OK', time.clock() - start, 'seconds')
        useHdrProbe = False
        start = time.clock()
        self.rayCounter = RayCountHelper(self.optix)
        self.oit = OitHelper(self.optix)
        self.raygen = trinity.Tr2OptixProgram(path + 'raygen.ptx', 'ray_request')
        shader = trinity.Tr2OptixProgram(path + 'vizualizer.ptx', 'closest_hit_VizGreen')
        viz_material = trinity.Tr2OptixMaterial()
        viz_material.SetClosestHit(0, shader)
        everything.append(viz_material)
        if False:
            any_hit_shadow = trinity.Tr2OptixProgram(path + 'shadow.ptx', 'any_hit_shadow')
            viz_material.SetAnyHit(1, any_hit_shadow)
            self.any_hit_shadow = any_hit_shadow
        else:
            self.any_hit_shadow = None
        start = time.clock()
        nameTranslation = {'GlowNormalSpecularMap': 'NormalMap'}

        def GroupByVertexBuffer(optixBatches):
            output = []
            for batchType in range(len(optixBatches)):
                batches = optixBatches[batchType]
                vbDict = {}
                for batch in batches:
                    vb = batch[2]
                    list = vbDict.get(vb, None)
                    if list is not None:
                        list.append(batch)
                    else:
                        vbDict[vb] = [batch]

                list = []
                for vb in vbDict.iterkeys():
                    list.append(vbDict[vb])

                output.append(list)

            return output

        cache = {}
        programs = {'skinned_tripleglowv3_48': 'triangle48',
         'singlev3_48': 'triangle48',
         'singleheatv3_48': 'triangle48',
         'tripleglowv3_40': 'triangle40',
         'singleheatv3_40': 'triangle40',
         'singlefresnelreflectionwithglow_56': 'triangle56',
         'doublefresnelreflectionwithglow_56': 'triangle56',
         'tripleglowoilv3_80': 'triangle80'}
        if False:
            nullintersect = trinity.Tr2OptixProgram(path + 'nullgeometry.ptx', 'intersect')
            nullbounds = trinity.Tr2OptixProgram(path + 'nullgeometry.ptx', 'bounds')
            everything.append(nullintersect)
            everything.append(nullbounds)
        mylogOK = set({})
        mylogFail = set({})
        linearNames = set({})
        linearNames.add('MaterialDiffuseColor')
        linearNames.add('MaterialReflectionColor')
        linearNames.add('MaskDiffuseColor')
        linearNames.add('MaskReflectionColor')
        linearNames.add('SubMaskDiffuseColor')
        linearNames.add('SubMaskReflectionColor')
        linearNames.add('GlowColor')
        topScene = trinity.Tr2OptixGroup()
        interopSamplerCache = {}
        for dynamic in scene.objects:
            if dynamic.__typename__ not in ('EveShip2', 'EveStation2'):
                continue
            model = dynamic
            if model.highDetailMesh is None or model.highDetailMesh.object is None:
                LogWarn('ship has no high detail meshes')
                continue
            skinnedOptix = optix.CreateFromEveSpaceObject2(model, 0, '', '', '')
            everything.append(skinnedOptix)
            optixBatches = skinnedOptix[0]
            self.objectsToRefresh[model] = skinnedOptix
            sorted = GroupByVertexBuffer(optixBatches)
            groups = []
            for batchType in range(len(optixBatches)):
                isOpaque = batchType == 0
                vbBatches = sorted[batchType]
                for batches in vbBatches:
                    groupChildren = []
                    for batch in batches:
                        effect = batch[1].effectFilePath.lower()
                        effect = effect[effect.rfind('/') + 1:]
                        effect = effect[:effect.rfind('.fx')]
                        ptx = programs.get(effect + '_' + str(batch[8]), '')
                        if ptx == '':
                            mylogFail.add(effect)
                            batch[0].SetIntersectProgram(nullintersect)
                            batch[0].SetBoundsProgram(nullbounds)
                            continue
                        mylogOK.add(effect)
                        intersect, bounds = cache.get(ptx, (None, None))
                        if intersect is None:
                            intersect = trinity.Tr2OptixProgram(path + ptx + '.ptx', 'intersect')
                            bounds = trinity.Tr2OptixProgram(path + ptx + '.ptx', 'bounds')
                            cache[ptx] = (intersect, bounds)
                        batch[0].SetIntersectProgram(intersect)
                        batch[0].SetBoundsProgram(bounds)
                        batchGeometryInstance = trinity.Tr2OptixGeometryInstance()
                        everything.append(batchGeometryInstance)
                        batchGeometryInstance.SetGeometry(batch[0])
                        if True:
                            material = self.CachedCreateMaterial(path, effect)
                            if material is None:
                                material = viz_material
                        else:
                            material = viz_material
                        batchGeometryInstance.SetMaterial(material)
                        SkinRaytracingTools.CopyParametersToContext(batch[1], batchGeometryInstance, linearNames)
                        groupChildren.append(batchGeometryInstance)
                        samplers = SkinRaytracingTools.InteropAllTexturesFromEffect(optix, batch[1], waitForFinish=True, nameTranslation=nameTranslation, scope=batchGeometryInstance, cache=interopSamplerCache)
                        everything.append(samplers)

                    group = trinity.Tr2OptixGeometryGroup()
                    group.SetChildCount(len(groupChildren))
                    for x in xrange(len(groupChildren)):
                        group.SetChild(x, groupChildren[x])

                    group.SetAcceleration('Bvh', 'Bvh')
                    self.objectsToMarkDirty.append(group)
                    groups.append(group)

                everything.append(cache)
                baseOffset = topScene.GetChildCount()
                topScene.SetChildCount(baseOffset + len(groups))
                for x in xrange(len(groups)):
                    topScene.SetChild(baseOffset + x, groups[x])

                everything.append(groups)

        if False:
            sphereGeometry = trinity.Tr2OptixGeometry()
            sphereGeometry.InitializeFromProgram(path + 'sphere_program.ptx', 'intersect', 'bounds')
            sphereGeometry.SetPrimitiveCount(1)
            everything.append(sphereGeometry)
            sphereInstance = trinity.Tr2OptixGeometryInstance()
            sphereInstance.SetGeometry(sphereGeometry)
            sphereInstance.SetMaterial(viz_material)
            sphereInstance.SetFloat4('pos_r', 0, 0, 0, 100)
            sphereInstance.SetFloat4('color_watt', 1, 0, 0, 1)
            everything.append(sphereInstance)
            group = trinity.Tr2OptixGeometryGroup()
            group.SetChildCount(1)
            group.SetChild(0, sphereInstance)
            group.SetAcceleration('Bvh', 'Bvh')
            topScene.SetChildCount(topScene.GetChildCount() + 1)
            topScene.SetChild(topScene.GetChildCount() - 1, group)
        everything.append(topScene)
        topScene.SetAcceleration('Bvh', 'Bvh')
        self.objectsToMarkDirty.append(topScene)
        optix.SetGroup('top_scene', topScene)
        optix.SetGroup('shadow_casters', topScene)
        if len(mylogOK) > 0:
            LogInfo('Converted succesfully:', str(mylogOK))
        else:
            LogWarn('No effects converted succesfully!')
        if len(mylogFail) > 0:
            LogWarn('Failed to convert:', str(mylogFail))
        if type(scene) == trinity.EveSpaceScene:
            c = SkinRaytracingTools.SafeLinearize(scene.sunDiffuseColor)
            optix.SetFloat4('SunDiffuseColor', c[0], c[1], c[2], c[3])
            c = scene.sunDirection
            optix.SetFloat4('SunDirWorld', -c[0], -c[1], -c[2], 0)
            c = SkinRaytracingTools.SafeLinearize(scene.ambientColor)
            optix.SetFloat4('SceneAmbientColor', c[0], c[1], c[2], c[3])
            c = SkinRaytracingTools.SafeLinearize(scene.fogColor)
            optix.SetFloat4('SceneFogColor', c[0], c[1], c[2], c[3])
        LogInfo('scene interop OK', time.clock() - start, 'seconds')
        start = time.clock()
        light = trinity.Tr2InteriorLightSource()
        if True:
            wattage = 2000000
            light.color = (1,
             1,
             1,
             wattage)
            light.radius = 50
            light.position = (200, 500, -300)
        else:
            wattage = 10000000
            light.color = (1,
             1,
             1,
             wattage)
            light.radius = 1000
            light.position = (0, 0, 0)
        bufEveLights = SkinRaytracingTools.CreateBufferForLights([], useHdrProbe, preserveAlpha=True)
        optix.SetBuffer('trinity_lights', bufEveLights)
        LogInfo('lights interop OK', time.clock() - start, 'seconds')
        if False:
            sphereGeometry = trinity.Tr2OptixGeometry()
            sphereGeometry.InitializeFromProgram(path + 'sphere_program.ptx', 'intersect', 'bounds')
            sphereGeometry.SetPrimitiveCount(1)
            sphereMaterial = trinity.Tr2OptixMaterial()
            sphereShader = trinity.Tr2OptixProgram(path + 'sphere_program.ptx', 'closest_hit_radiance')
            sphereMaterial.SetClosestHit(0, sphereShader)
            sphereInstance = trinity.Tr2OptixGeometryInstance()
            sphereInstance.SetGeometry(sphereGeometry)
            sphereInstance.SetMaterial(sphereMaterial)
            sphereInstance.SetFloat4('pos_r', light.position[0], light.position[1], light.position[2], light.radius)
            sphereInstance.SetFloat4('color_watt', light.color[0], light.color[1], light.color[2], light.color[3])
            n = topScene.GetChildCount()
            topScene.SetChildCount(n + 1)
            sphereGroup = trinity.Tr2OptixGeometryGroup()
            sphereGroup.SetChildCount(1)
            sphereGroup.SetChild(0, sphereInstance)
            sphereGroup.SetAcceleration('Bvh', 'Bvh')
            topScene.SetChild(n, sphereGroup)
        start = time.clock()
        optix.SetRayGenerationProgram(0, self.raygen)
        optix.SetEntryPointCount(1)
        miss = None
        if not useHdrProbe:
            miss = trinity.Tr2OptixProgram(path + 'eve_miss.ptx', 'miss')
        else:
            miss = trinity.Tr2OptixProgram(path + 'eve_miss_probe.ptx', 'miss')
        optix.SetMissProgram(3, miss)
        optix.SetFloat3('bg_color', 1.0, 0, 0)
        everything.append(miss)
        if False:
            exception = trinity.Tr2OptixProgram(path + 'eve_miss.ptx', 'exception')
            optix.SetExceptionProgram(0, exception)
            everything.append(exception)
        optix.SetStackSize(4096)
        self.everything = everything
        SkinRaytracingTools.SetOptixMatrixFromTrinity(optix, 'clipToWorld', self.width / float(self.height))
        LogInfo('general setup OK', time.clock() - start, 'seconds')
        optix.ReportObjectCounts()
        start = time.clock()
        optix.Compile()
        LogInfo('compile OK', time.clock() - start, 'seconds')
        start = time.clock()
        optix.Validate()
        LogInfo('validate OK', time.clock() - start, 'seconds')
        start = time.clock()
        optix.Run(0, 0, 0)
        LogInfo('BVH OK', time.clock() - start, 'seconds')
        start = time.clock()
        if False:
            self.blitfx.SetTexture(outputTexture, self.highpassRT, self.filteredRT)
        else:
            self.blitfx.SetTexture(outputTexture, outputTexture, outputTexture)
        rj = trinity.CreateRenderJob('ShipOptixRenderer')
        self.AddCallback(ShipOptixRenderer.RaytraceFrame, 'Raytrace Frame', rj)
        rj.SetStdRndStates(trinity.RM_FULLSCREEN).name = 'fullscreen state'
        if False:
            rj.SetRenderTarget(self.highpassRT.wrappedRenderTarget).name = '  SetRT highpassRT'
            rj.RenderEffect(self.blitfx.highpassEffect).name = '           high pass'
            rj.SetRenderTarget(self.filteredRT.wrappedRenderTarget).name = '  SetRT filteredRT'
            rj.RenderEffect(self.blitfx.gaussianHorizEffect).name = '           horizontal blur'
            rj.SetRenderTarget(self.highpassRT.wrappedRenderTarget).name = '  SetRT highpassRT'
            rj.RenderEffect(self.blitfx.gaussianVertEffect).name = '           vertical blur'
        rj.SetStdRndStates(trinity.RM_FULLSCREEN).name = 'fullscreen state'
        rj.RenderEffect(self.blitfx.effect).name = '           blit'
        tp2 = None
        for job in trinity.renderJobs.recurring:
            if job.name == 'TrinityPanel:View1':
                tp2 = job

        if tp2 is None:
            rj.ScheduleRecurring(insertFront=False)
        else:
            final = None
            for step in tp2.steps:
                if step.name == 'SET_FINAL_RT':
                    final = step
                    break

            if final is not None:
                tp2.steps.insert(tp2.steps.index(final), trinity.TriStepRunJob(rj))
            else:
                tp2.steps.append(trinity.TriStepRunJob(rj))
        self.renderJob = rj
        LogInfo('final setup OK', time.clock() - start, 'seconds')
        FullOptixRenderer.EnablePaperDollJobs(False)

    def ApplySettings(self):
        self.optix.SetFloat('light_size', self.settings['light_size'])
        self.optix.SetFloat3('depthOfField', 1.0, self.settings['lens_radius'], 0)
        self.optix.SetFloat('HairShadows', self.settings['HairShadows'])
        self.optix.SetFloat('EnvMapBoost', self.settings['EnvMapBoost'] / 3.1415927)
        self.previousVP.Identity()

    def SetLensRadius(self, lens_radius):
        self.settings['lens_radius'] = lens_radius
        self.ApplySettings()

    def SetLensFocalDistance(self, lens_focal_distance):
        if lens_focal_distance <= 0:
            self.settings.pop('lens_focal_distance', 0)
        else:
            self.settings['lens_focal_distance'] = lens_focal_distance
        self.ApplySettings()

    def SetLightSize(self, light_size):
        self.settings['light_size'] = light_size
        self.ApplySettings()

    def SetHairShadowsEnabled(self, enabled):
        self.settings['HairShadows'] = float(enabled)
        self.ApplySettings()

    def SetBackgroundIntensity(self, intensity):
        self.settings['EnvMapBoost'] = intensity
        self.ApplySettings()

    def __init__(self, scene = None, backgroundBitmap = None, memento = None, beardLength = (0.01, 0.01), beardGravity = 0.0005, outputWidth = None, outputHeight = None, asyncSetup = True, listenForUpdate = True):
        LogInfo('init', self)
        blue.motherLode.maxMemUsage = 0
        blue.resMan.ClearAllCachedObjects()
        self.framecount = 0
        self.listenForUpdate = listenForUpdate
        self.everything = None
        self.objectsToRefresh = {}
        self.objectsToMarkDirty = []
        if memento is not None:
            self.settings = memento
        else:
            self.settings = {}
            self.settings['light_size'] = 0.125
            self.settings['lens_radius'] = 0.001
            self.settings['HairShadows'] = 1.0
            self.settings['EnvMapBoost'] = 1.0
            self.settings['backgroundBitmap'] = backgroundBitmap if backgroundBitmap is not None else 'res:/texture/global/red_blue_ramp.dds'
            self.settings['beardLength'] = beardLength
            self.settings['beardGravity'] = beardGravity
            if outputWidth is not None:
                self.settings['outputWidth'] = outputWidth
            if outputHeight is not None:
                self.settings['outputHeight'] = outputHeight
        if asyncSetup:
            uthread.new(self._DoInit, scene=scene)
        else:
            self._DoInit(scene=scene)

    def GetMemento(self):
        return self.settings

    def __del__(self):
        LogInfo('deleting', self)
        if hasattr(self, 'renderJob'):
            self.renderJob.UnscheduleRecurring()
            self.renderJob = None
        del self.any_hit_shadow
        del self.raygen
        del self.rayCounter
        del self.oit
        del self.shBuffer
        del self.outputBuffer
        del self.everything
        del self.objectsToRefresh
        del self.objectsToMarkDirty
        self.optix.ClearObjects()
        LogInfo('Post-cleanup leak check:')
        self.optix.ReportObjectCounts()
        FullOptixRenderer.EnablePaperDollJobs(True)

    def RefreshMatrices(self):
        for ship, optixList in self.objectsToRefresh.iteritems():
            self.optix.RefreshMatrices(ship, optixList)

        for dirty in self.objectsToMarkDirty:
            dirty.MarkDirty()

        self.ApplySettings()
        LogInfo('Refreshed')

    @staticmethod
    def Pause():
        if FullOptixRenderer.instance is not None:
            FullOptixRenderer.instance.renderJob.UnscheduleRecurring()

    @staticmethod
    def NotifyUpdate():
        if FullOptixRenderer.instance is not None and FullOptixRenderer.instance.listenForUpdate:
            LogInfo('NotifyUpdate, restarting', FullOptixRenderer.instance)
            memento = FullOptixRenderer.instance.GetMemento()
            FullOptixRenderer.instance = None
            FullOptixRenderer.instance = FullOptixRenderer(memento=memento)