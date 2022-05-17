from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId

class GreedyBot(BotAI):

    def __init__(self):
        self.rush = False

    async def warp_new_voidrays(self, proxy):
        for sg in self.structures(UnitTypeId.STARGATE).ready:

            abilities = await self.get_available_abilities(sg)

            if AbilityId.STARGATETRAIN_VOIDRAY in abilities:
                pos = proxy.position.to2.random_on_distance(6)
                sg.train(UnitTypeId.VOIDRAY)

    async def on_step(self, iteration: int): 
        # make the workers work?
        await self.distribute_workers()

        if not self.townhalls.ready: # if no nexuses left, attack enemy base
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return

        nexus = self.townhalls.ready.random # only one should exist with the current strategy

        # Build pylon when on low supply
        if self.supply_left < 8 and self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)
            return

        # 16 for minerals, 3 on each gas is ideal, not sure what distribute_workers will do
        if self.workers.amount <= self.townhalls.amount * 22 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        elif self.structures(UnitTypeId.PYLON).amount < 5 and self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 5))

        proxy = None
        if self.structures(UnitTypeId.PYLON).ready:
            proxy = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])

            # get a random ready PYLON
            pylon = self.structures(UnitTypeId.PYLON).ready.random

            # Build a GATEWAY, unlocks: CYBERNETICSCORE
            if (self.can_afford(UnitTypeId.GATEWAY) and self.structures(UnitTypeId.GATEWAY).amount < 1):
                await self.build(UnitTypeId.GATEWAY, near=pylon)

            # If no CYBERNETICSCORE, build one
            if self.structures(UnitTypeId.GATEWAY).ready:
                if not self.structures(UnitTypeId.CYBERNETICSCORE):
                    if (self.can_afford(UnitTypeId.CYBERNETICSCORE)and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
            
            # If no STARGATE, build one
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready:
                if not self.structures(UnitTypeId.STARGATE):
                    if (self.can_afford(UnitTypeId.STARGATE)and self.already_pending(UnitTypeId.STARGATE) == 0):
                        await self.build(UnitTypeId.STARGATE, near=pylon)

        # Build gas
        for nexus in self.townhalls.ready:
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:

                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)

                if worker is None:
                    break

                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)
        
        if self.structures(UnitTypeId.STARGATE).ready:
            await self.warp_new_voidrays(proxy)

        # Chrono Nexus for faster prob production?
        if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not nexus.is_idle:
            if nexus.energy >= 50:
                nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
                print("Nexus is chrono boosted now!, -50 energy")    

        # Launch a greedy attack when enough VOIDRAYS
        if self.units(UnitTypeId.VOIDRAY).amount >= 15 or self.rush:
            self.rush = True
            for vr in self.units(UnitTypeId.VOIDRAY).ready.idle:
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(vr)
                    vr.attack(target)
                else:
                    vr.attack(self.enemy_start_locations[0])

        # If less than enough VOIDRAYS, respond only to enemy near nexus
        elif(self.units(UnitTypeId.VOIDRAY).amount > 0):
            for vr in self.units(UnitTypeId.VOIDRAY).ready.idle:
                targets = self.enemy_units.closer_than(25, nexus)
                if targets:
                    target = targets.closest_to(vr)
                    vr.attack(target)
                
"""
run_game(maps.get("BlackburnAIE"), [
    Bot(Race.Protoss, GreedyBot()),
    Bot(Race.Protoss, GreedyBot())
    ], realtime=False)
"""
