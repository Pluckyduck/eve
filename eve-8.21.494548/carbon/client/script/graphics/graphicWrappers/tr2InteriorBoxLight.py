#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/graphics/graphicWrappers/tr2InteriorBoxLight.py
import graphicWrappers
import trinity
import util
import weakref
import geo2

class Tr2InteriorBoxLight(util.BlueClassNotifyWrap('trinity.Tr2InteriorBoxLight')):
    __guid__ = 'graphicWrappers.Tr2InteriorBoxLight'

    @staticmethod
    def Wrap(triObject, resPath):
        Tr2InteriorBoxLight(triObject)
        triObject.AddNotify('color', triObject._TransformChange)
        triObject.AddNotify('rotation', triObject._TransformChange)
        triObject.AddNotify('transform', triObject._TransformChange)
        triObject.AddNotify('falloff', triObject._TransformChange)
        triObject.scene = None
        return triObject

    def AddToScene(self, scene):
        if self.scene and self.scene():
            scene.RemoveLight(self.scene())
        scene.AddLight(self)
        self.scene = weakref.ref(scene)

    def RemoveFromScene(self, scene):
        scene.RemoveLight(self)
        self.scene = None

    def _TransformChange(self, transform):
        self.OnTransformChange()

    def OnTransformChange(self):
        pass

    def SetPosition(self, position):
        self.position = position

    def GetPosition(self):
        return self.position

    def GetRotationYawPitchRoll(self):
        return geo2.QuaternionRotationGetYawPitchRoll(self.rotation)

    def SetRotationYawPitchRoll(self, ypr):
        self.rotation = geo2.QuaternionRotationSetYawPitchRoll(*ypr)

    def SetScaling(self, scaling):
        self.scaling = scaling

    def GetScaling(self):
        return self.scaling

    def GetColor(self):
        return self.color[:3]

    def SetColor(self, color):
        self.color = (color[0],
         color[1],
         color[2],
         1)

    def GetFalloff(self):
        return self.falloff

    def SetFalloff(self, falloff):
        self.falloff = falloff