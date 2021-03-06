#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/Jump.py
import effects
import blue
import uthread

class JumpDriveIn(effects.ShipEffect):
    __guid__ = 'effects.JumpDriveIn'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if shipBall is None:
            self.sfxMgr.LogError(self.__guid__, ' could not find a ball')
            return
        self.PlayOldAnimations(self.gfx)

    def DelayedHide(self, shipBall, delay):
        blue.pyos.synchro.SleepSim(delay)
        if shipBall is not None and shipBall.model is not None:
            shipBall.model.display = False


class JumpDriveInBO(JumpDriveIn):
    __guid__ = 'effects.JumpDriveInBO'


class JumpDriveOut(JumpDriveIn):
    __guid__ = 'effects.JumpDriveOut'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if eve.session.shipid == shipID:
            if hasattr(shipBall, 'KillBooster'):
                shipBall.KillBooster()
        self.PlayOldAnimations(self.gfx)
        uthread.new(self.DelayedHide, shipBall, 180)


class JumpDriveOutBO(JumpDriveOut):
    __guid__ = 'effects.JumpDriveOutBO'


class JumpIn(JumpDriveIn):
    __guid__ = 'effects.JumpIn'

    def Start(self, duration):
        scaling = self.gfxModel.scaling
        self.gfxModel.scaling = (scaling[0] * 0.005, scaling[1] * 0.005, scaling[2] * 0.005)
        JumpDriveIn.Start(self, duration)


class JumpOut(effects.ShipEffect):
    __guid__ = 'effects.JumpOut'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        uthread.new(self.DelayedHide, shipBall)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if eve.session.shipid == shipID:
            if hasattr(shipBall, 'KillBooster'):
                shipBall.KillBooster()
        if hasattr(self.gfx, 'scaling'):
            radius = shipBall.radius
            self.gfx.scaling = (radius, radius, radius)
            self.gfxModel.scaling = (1, 1, 1)
        listener = None
        for obs in self.gfx.observers:
            if obs.observer.name.startswith('effect_'):
                listener = obs.observer

        for curveSet in targetBall.model.curveSets:
            if curveSet.name == 'GateActivation':
                for curve in curveSet.curves:
                    if curve.name == 'audioEvents':
                        curve.eventListener = listener

        self.PlayNamedAnimations(targetBall.model, 'GateActivation')

    def DelayedHide(self, shipBall):
        blue.pyos.synchro.SleepSim(880)
        self.fxSequencer.OnSpecialFX(shipBall.id, None, None, None, None, None, 'effects.Uncloak', 0, 0, 0)
        if shipBall is not None and shipBall.model is not None:
            shipBall.model.display = False


class JumpOutWormhole(JumpDriveIn):
    __guid__ = 'effects.JumpOutWormhole'

    def Start(self, duration):
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        if getattr(shipBall, 'model', None) is not None:
            self.fxSequencer.OnSpecialFX(shipID, None, None, None, None, None, 'effects.CloakRegardless', 0, 1, 0, -1, None)
        uthread.new(self.DelayedHide, shipBall, 2000)
        wormholeID = self.ballIDs[1]
        wormholeBall = self.fxSequencer.GetBall(wormholeID)
        if eve.session.shipid == shipID:
            if hasattr(shipBall, 'KillBooster'):
                shipBall.KillBooster()
        if hasattr(self.gfx, 'scaling'):
            radius = shipBall.radius
            self.gfx.scaling = (radius, radius, radius)
            self.gfxModel.scaling = (1, 1, 1)
        self.PlayNamedAnimations(wormholeBall.model, 'Activate')
        wormholeBall.PlaySound('worldobject_wormhole_jump_play')


class GateActivity(effects.GenericEffect):
    __guid__ = 'effects.GateActivity'

    def Prepare(self):
        gateBall = self.GetEffectShipBall()
        self.gfx = gateBall.model
        self.AddSoundToEffect(2)

    def Start(self, duration):
        gateID = self.ballIDs[0]
        gateBall = self.fxSequencer.GetBall(gateID)
        if gateBall is None:
            self.sfxMgr.LogError('GateActivity could not find a gate ball')
            return
        if gateBall.model is None:
            self.sfxMgr.LogError('GateActivity could not find a gate ball')
            return
        self.PlayNamedAnimations(gateBall.model, 'GateActivation')

    def Stop(self):
        self.gfx.observers.remove(self.observer)
        self.observer.observer = None


class WormholeActivity(effects.GenericEffect):
    __guid__ = 'effects.WormholeActivity'

    def Start(self, duration):
        wormholeID = self.ballIDs[0]
        wormholeBall = self.fxSequencer.GetBall(wormholeID)
        if wormholeBall is None:
            self.sfxMgr.LogError('WormholeActivity could not find a wormhole ball')
            return
        if wormholeBall.model is None:
            self.sfxMgr.LogError('WormholeActivity could not find a wormhole ball')
            return
        self.PlayNamedAnimations(wormholeBall.model, 'Activate')
        wormholeBall.PlaySound('worldobject_wormhole_jump_play')