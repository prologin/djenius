import {Ability, AbilityBuilder} from '@casl/ability';

const objectName = 'all';

export const Capability = {
    UpVote: 'UpVote',
    DownVote: 'DownVote',
    Search: 'Search',
    Suggest: 'Suggest',
    Ban: 'Ban',
    Accept: 'Accept',
    Pause: 'Pause',
    Seek: 'Seek',
    Volume: 'Volume',
    Skip: 'Skip',
    AdminQueue: 'AdminQueue',
    EventLog: 'EventLog',
};

export const ControlCapabilities = [Capability.Volume, Capability.Seek, Capability.Skip, Capability.Pause];

function defineAbilities(userState) {
    const {can, rules} = AbilityBuilder.extract();
    console.log("defined capabilities for", userState.name, userState.caps);
    for (let abilityName of userState.caps) {
        can(abilityName, objectName);
    }
    return rules;
}

const ability = new Ability([]);

export function updateAbilities(userState) {
    ability.update(defineAbilities(userState));
}

export function can(perm) {
    return ability.can(perm, objectName);
}

export default ability;
