from sc2 import maps
from sc2.player import Bot, Computer
from sc2.main import run_game
from sc2.data import Race, Difficulty
from sc2.bot_ai import BotAI
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId

class StalkerCheeseBot(BotAI):
    def __init__(self):
        # self.unit_command_uses_self_do = True # actually disables everything!?
        self.nexus = None
        self.chronoboost_count = 0
        self.scout_probe = None
        self.stalker_count = 0
        self.warpgate_researched = False
        self.sneaky_pylon_placement = None
        self.sneaky_pylon_placed = False
        self.researched_blink = False
        self.rush_stalkers = False

        self.max_enemy_count = 4
        self.BLINK_HP_PERCENTAGE = 0.5

    async def getTwilightCouncil(self):
        placement = await self.find_placement(UnitTypeId.TWILIGHTCOUNCIL, near=self.nexus.position, placement_step=1)
        if placement is None:
            return
        await self.build(UnitTypeId.TWILIGHTCOUNCIL, placement)
        await self._client.move_camera(placement)
        return

    async def researchBlink(self):
        if(self.researched_blink == False and self.can_afford(AbilityId.RESEARCH_BLINK)):
            if(self.researched_blink == False):
                try: 
                    tw_council = self.structures(UnitTypeId.TWILIGHTCOUNCIL).ready.first
                except:
                    return
                print("Blink research started")
                self.do(tw_council(AbilityId.RESEARCH_BLINK))
                print("Blink research ended")
                self.researched_blink = True
                

    async def warp_new_units(self, proxy):
        for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
            pos = proxy.position.to2.random_on_distance(4)
            placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
            if placement is None:
                return
            self.do(warpgate.warp_in(UnitTypeId.STALKER, placement))
        return

    async def expand_now_custom(self):
        # Expand new nexuses
        if(not self.already_pending(UnitTypeId.NEXUS) and self.can_afford(UnitTypeId.NEXUS)):
            await self.expand_now()
            print('Built one more nexus')

        # Build probes for these nexuses
        for nexus in self.townhalls.ready:
            if self.can_afford(UnitTypeId.PROBE) and nexus.is_idle:
                if(not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST)):
                    if nexus.energy >= 50:
                        self.nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.nexus)
                nexus.train(UnitTypeId.PROBE)


            # Extract resources with these new nexuses
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
                    break
        return

    async def on_step(self, iteration: int):
        # print("Stalker amount:", self.units(UnitTypeId.STALKER).ready.amount)
        await self.distribute_workers(resource_ratio=1.25)
        
        """
        if(self.nexus == None):
            self.nexus = self.townhalls.random 
        """
        if(self.townhalls.ready.amount > 0):
            self.nexus = self.townhalls.ready.random
        else:
            return

        if(self.supply_used < 23 and self.nexus.is_idle):
            if self.can_afford(UnitTypeId.PROBE) and self.already_pending(UnitTypeId.PROBE) == 0:
                self.nexus.train(UnitTypeId.PROBE)
        if(self.workers.amount >= 17 and self.scout_probe == None and self.can_afford(UnitTypeId.PYLON) and self.warpgate_researched and not self.scout_probe):
            # I didn't know how to make the probe go there and stay until we have the warpgate researched :/
            self.scout_probe = self.workers.closest_to(self.enemy_start_locations[0])
            self.workers.remove(self.scout_probe)
            closest = None
            min_dist = 10000
            for loc in self.expansion_locations_list:
                dist = self.enemy_start_locations[0].distance_to(loc)
                if(dist < min_dist and dist > 30):
                    min_dist = dist
                    closest = loc

            print("Sneaking a probe")

            self.sneaky_pylon_placement = await self.find_placement(UnitTypeId.PYLON, near=closest, placement_step=1)
            self.scout_probe.build(UnitTypeId.PYLON, self.sneaky_pylon_placement, queue=True)
            await self._client.move_camera(self.sneaky_pylon_placement)
            self.sneaky_pylon_placed = True
            
        if(self.already_pending(UnitTypeId.GATEWAY) and self.chronoboost_count == 0):
            if not self.nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                if self.nexus.energy >= 50:
                    self.nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.nexus)
                    await self._client.move_camera(self.nexus)
                    print("Nexus is chrono boosted now!, -50 energy")
                    self.chronoboost_count += 1

        if(self.supply_used == 14):
            placement = self.nexus.position.towards(self.game_info.map_center, 5)
            builder_prob = self.workers.closest_to(placement)
            if(self.already_pending(UnitTypeId.PYLON) == 0 and self.can_afford(UnitTypeId.PYLON)):
                builder_prob.build(UnitTypeId.PYLON, placement)
                await self._client.move_camera(placement)
            return
        elif(self.supply_used == 16):
            placement = self.structures(UnitTypeId.PYLON).random.position.towards(self.game_info.map_center, 4)
            builder_prob = self.workers.closest_to(placement)
            if(self.already_pending(UnitTypeId.GATEWAY) == 0 and self.can_afford(UnitTypeId.GATEWAY)):
                builder_prob.build(UnitTypeId.GATEWAY, placement)
                await self._client.move_camera(placement)
        elif(self.supply_used == 17):
            vgs = self.vespene_geyser.closer_than(15, self.nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break
                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)
                    break
        elif(self.supply_used == 18):
            vgs = self.vespene_geyser.closer_than(15, self.nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break
                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)
                    break
        elif(self.supply_used == 20):
            gateway_count = self.already_pending(UnitTypeId.GATEWAY) + self.structures(UnitTypeId.GATEWAY).ready.amount
            if(gateway_count == 1 and self.can_afford(UnitTypeId.GATEWAY)):
                pos = self.structures(UnitTypeId.GATEWAY).random.position
                placement_position = await self.find_placement(UnitTypeId.GATEWAY, near=pos, placement_step=1)
                builder_prob = self.workers.closest_to(placement_position)
                builder_prob.build(UnitTypeId.GATEWAY, placement_position)
                await self._client.move_camera(placement_position)
        elif(self.supply_used == 21):
            if(not self.already_pending(UnitTypeId.CYBERNETICSCORE) and self.structures(UnitTypeId.GATEWAY).amount > 0):
                placement_position = await self.find_placement(UnitTypeId.CYBERNETICSCORE, near=self.structures(UnitTypeId.GATEWAY).random.position, placement_step=1)
                builder_prob = self.workers.closest_to(placement_position)
                builder_prob.build(UnitTypeId.CYBERNETICSCORE, placement_position)
                await self._client.move_camera(placement_position)
        elif(self.supply_used == 22):
            if(not self.already_pending(UnitTypeId.PYLON)):
                placement_position = await self.find_placement(UnitTypeId.PYLON, near=self.structures(UnitTypeId.ASSIMILATOR).random.position, placement_step=1)
                builder_prob = self.workers.closest_to(placement_position)
                builder_prob.build(UnitTypeId.PYLON, placement_position)
                await self._client.move_camera(placement_position)
        elif(self.supply_used == 23 and self.structures(UnitTypeId.GATEWAY).ready.amount == 2 and self.stalker_count == 0 and self.structures(UnitTypeId.CYBERNETICSCORE).ready.amount == 1):
            gateways = self.structures(UnitTypeId.GATEWAY).ready
            for gw in gateways:
                gw.train(UnitTypeId.STALKER)
                self.stalker_count += 1
                
        elif(self.supply_used == self.supply_cap):
            if self.can_afford(UnitTypeId.PYLON):
                # get pylon closest to enemy base, but not the sneaky pylon
                if(self.units(UnitTypeId.PYLON).amount > 0):
                    pos = self.units(UnitTypeId.PYLON).closer_than(50,self.townhalls.ready.first).closest_to(self.enemy_start_locations[0]).towards(self.enemy_start_locations[0])
                    placement_position = await self.find_placement(UnitTypeId.GATEWAY, near=pos, placement_step=1)
                else:
                    placement_position = self.nexus
                await self.build(UnitTypeId.PYLON, near=placement_position)
                await self._client.move_camera(placement_position)
                print('out of resources! new PYLON')

        if self.structures(UnitTypeId.CYBERNETICSCORE).ready.amount > 0 and self.can_afford(AbilityId.RESEARCH_WARPGATE) and not self.warpgate_researched:
            ccore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            self.do(ccore(AbilityId.RESEARCH_WARPGATE))
            self.warpgate_researched = True

        if(self.stalker_count >= 2):
            gateway_count = self.already_pending(UnitTypeId.GATEWAY) + self.structures(UnitTypeId.GATEWAY).ready.amount 
            gateway_count += self.already_pending(UnitTypeId.WARPGATE) + self.structures(UnitTypeId.WARPGATE).ready.amount
            if(gateway_count < 4):
                placement_position = await self.find_placement(UnitTypeId.GATEWAY, near=self.structures(UnitTypeId.PYLON).random.position, placement_step=1)
                if not placement_position:
                    return
                builder_prob = self.workers.closest_to(placement_position)
                builder_prob.build(UnitTypeId.GATEWAY, placement_position)
                await self._client.move_camera(placement_position)
            for st in self.units(UnitTypeId.STALKER):
                targets = self.enemy_units.closer_than(30, self.nexus)
                if(targets.count == 1):
                    break
                if targets:
                    target = targets.closest_to(st)
                    if(st.health_percentage < self.BLINK_HP_PERCENTAGE):
                        # print("tying to blink, hp left: ", st.health_percentage)
                        await self._client.move_camera(st.position)
                        blink_pos = st.position + (target.position - st.position).normalized * 8
                        st(AbilityId.EFFECT_BLINK_STALKER, blink_pos)
                    st.attack(target)

        if(self.units(UnitTypeId.STALKER).amount > self.structures(UnitTypeId.NEXUS).amount * 13):
            await self.expand_now_custom()
        elif(self.vespene > 1000 and self.minerals > 2000):
            await self.expand_now_custom()
        else:
            # WARP NEW UNITS
            if(self.structures(UnitTypeId.WARPGATE).ready.amount >= 4 and self.can_afford(UnitTypeId.NEXUS)):
                proxy = self.structures(UnitTypeId.PYLON).closest_to(self.sneaky_pylon_placement)
                await self.warp_new_units(proxy)
                if(self.structures(UnitTypeId.TWILIGHTCOUNCIL).amount == 0 and self.researched_blink == False and self.can_afford(UnitTypeId.TWILIGHTCOUNCIL)):
                    if(self.already_pending(UnitTypeId.TWILIGHTCOUNCIL) == False):
                        await self.getTwilightCouncil()
                await self.researchBlink()
        
        enemy_army_count = self.enemy_units.filter(lambda unit: unit.can_be_attacked).amount
        if(enemy_army_count > self.max_enemy_count):
            self.max_enemy_count = enemy_army_count

        # attack!    
        if self.units(UnitTypeId.STALKER).amount >= self.max_enemy_count + 2 or self.rush_stalkers:
            self.rush_stalkers = True
            for st in self.units(UnitTypeId.STALKER):
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(st)
                    if(st.health_percentage < self.BLINK_HP_PERCENTAGE):
                        # print("tying to blink, hp left: ", st.health_percentage)
                        await self._client.move_camera(st.position)
                        blink_pos = st.position + (target.position - st.position).normalized * 8
                        st(AbilityId.EFFECT_BLINK_STALKER, blink_pos)
                    st.attack(target)
                else:
                    # do not see targets, better not blink
                    st.attack(self.enemy_start_locations[0])

run_game(maps.get("BerlingradAIE"), [
    Bot(Race.Protoss, StalkerCheeseBot(), name="Cheeser"),
    Computer(Race.Protoss, Difficulty.Harder)
    ], realtime=False,
    save_replay_as="Example.SC2Replay")