import fetch from 'node-fetch';

export async function getPressReferneces(
    entity_id,
    crunchbase_api_key,
    after_id = null,
    base = "https://api.crunchbase.com/api/v4",
    timeout = 10000) {
    let url = `${base}/entities/organizations/${entity_id}/cards/press_references?order=posted_on%20desc`;

    const controller = new AbortController();
    if (after_id) {
        url = `${url}/&after_id=${after_id}`;
    }
    const id = setTimeout(
        () => controller.abort(), timeout);
    const response = await fetch(url, {
        headers: {
            "accept": "application/json",
            "x-cb-user-key": crunchbase_api_key,
        },
        signal: controller.signal
    });
    clearTimeout(id);
    if (response.status != 200)
        throw response.status;
    return response.json();
}

class PressReference {
    constructor(organizationIdentity, pressReference) {
        this.organizationIdentity = organizationIdentity;
        this.pressReference = pressReference;
    }

    getOrganizationId() {
        return this.organizationIdentity;
    }

    getAuthor() {
        return this.pressReference.author;
    }

    getIdentifier() {
        return this.pressReference.identifier.uuid;
    }

    getSummary() {
        return this.pressReference.identifier.value;
    }
    getUrl() {
        return this.pressReference.url.value;
    }
    getPostedOnStr() {
        return this.pressReference.posted_on;
    }
    /**
     * 
     * @param  postedOnDate Date type.
     */
    isEqOrGreaterThan(postedOnDate) {
        return postedOnDate <= this.#getPostedOn();
    }

    getPostedOn() {
        return new Date(this.getPostedOnStr());
    }
}

export class PressReferences {

    constructor(pressReferences) {
        this.pressReferences = pressReferences;
    }

    *[Symbol.iterator]() {
        for (const reference of this.pressReferences) {
            yield reference;
        }
    }

    length() {
        return this.pressReferences.length;
    }

    filterOldByPostedOnDate(postedOnDateStr) {
        const date = Date.parse(postedOnDateStr);
        if (Number.isNaN(date))
            throw `${postedOnDateStr} is not in the format of YYYY-MM-DD.`;

        const filtered = this.pressReferences.filter(
            item => item.isEqOrGreaterThan(date));
        return new PressReferences(item);
    }

    getAuthors() {
        return this.pressReferences.map(item => item.getAuthor());
    }
    getOrganizationIds() {
        return this.pressReferences.map(item => item.getOrganizationId());
    }
    getIdentifiers() {
        return this.pressReferences.map(item => item.getIdentifier())
    }
    getSummaries() {
        return this.pressReferences.map(item => item.getSummary())
    }
    getUrls() {
        return this.pressReference.map(item => item.getUrl());
    }
    getPostedOnStrs() {
        return this.pressReference.map(item => item.getPostedOnStr());
    }

    getOldestIdentifier() {
        if (this.length == 0)
            return null;
        let id = this.pressReferences[0].getIdentifier();
        let postedOn = this.pressReferences[0].getPostedOn();
        for (const reference of this) {
            if (!reference.isEqOrGreaterThan(postedOn)) {
                postedOn = reference.postedOnDate();
                id = reference.getIdentifier();
            }
        }
        return id;
    }
}


function createPressReferences(response) {
    const organizationId = response.properties.identifier.value;
    const pressReferences = response.cards.press_references;

    return new PressReferences(
        pressReferences.map(
            item => new PressReference(organizationId, item))
    );
}
