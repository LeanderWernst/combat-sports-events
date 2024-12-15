<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import ical from 'ical';
import 'primeicons/primeicons.css';
import { FilterMatchMode } from '@primevue/core/api';

interface Event {
    org: string;
    summary: string;
    start: Date;
    end: Date;
    location: string;
    details: string;
}

const props = defineProps<{
    files: string[];
}>();

const events = ref<Event[]>([]);
const selectedEvent = ref<Event | null>(null);
const expandedRows = ref([]);
const currentPage = ref(0);
const selectedFilters = ref<string[]>([]);
const hour12 = ref(false);
const darkmode = ref(false);

const loadICS = async (file: string) => {
    try {
        const response = await fetch(`https://raw.githubusercontent.com/LeanderWernst/combat-sports-event-scraper/refs/heads/main/ics/${file}`);
        /* const response = await fetch(`./ics/${file}`); */
        const icsText = await response.text();
        const jcalData = ical.parseICS(icsText);

        const parsedEvents = Object.values(jcalData)
            .filter((event: any) => event.type === 'VEVENT')
            .map((event: any) => ({
                org: file.split('_')[0], //event.summary.toString().split(' ')[0],
                summary: event.summary || `No Title found (${Math.random()})`,
                start: new Date(event.start),
                end: new Date(event.end),
                location: event.location || 'n/a',
                details: event.url
            }));

        events.value.push(...parsedEvents);
    } catch (error) {
        console.error('Error loading ICS file:', error);
    }
};

const groupedEvents = computed(() => {
    const groups = new Map<string, Event[]>();

    // Group events by month key
    events.value.forEach(event => {
        const monthKey = `${event.start.getFullYear()}-${String(event.start.getMonth() + 1).padStart(2, '0')}`;
        if (!groups.has(monthKey)) {
            groups.set(monthKey, []);
        }
        groups.get(monthKey)?.push(event);
    });

    // Filter events based on selected filters
    const filteredEvents = selectedFilters.value.length > 0
        ? events.value.filter(event => selectedFilters.value.includes(event.org))
        : events.value;

    // Filter events but maintain empty groups
    const filteredGroups = new Map<string, Event[]>();
    groups.forEach((groupEvents, monthKey) => {
        const filteredGroupEvents = groupEvents.filter(event => filteredEvents.includes(event));
        filteredGroups.set(monthKey, filteredGroupEvents);
    });

    // Sort the groups by month key
    const sortedGroups = Array.from(filteredGroups.entries()).sort(([keyA], [keyB]) => {
        return keyA.localeCompare(keyB);
    });

    return sortedGroups;
});


const currentMonthIndex = computed(() => {
    const now = new Date();
    const currentKey = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    return groupedEvents.value.findIndex(([key]) => key === currentKey);
});

const toggleFilter = (promo: string) => {
    const index = selectedFilters.value.indexOf(promo);
    if (index > -1) {
        selectedFilters.value.splice(index, 1);
    } else {
        selectedFilters.value.push(promo);
        if (selectedFilters.value.length == promoList.value.length) {
            selectedFilters.value = []
        }
    }    
    
    selectNextUpcomingEvent();
};

const promoList = computed(() => {
    return Array.from(new Set(events.value.map(event => event.org)));
});

const selectNextUpcomingEvent = () => {
    const now = new Date();

    const currentGroupedEvents = groupedEvents.value[currentPage.value]?.[1] || [];

    const nextEvent = currentGroupedEvents
        .filter(event => event.start >= now && event.end > now)
        .sort((a, b) => a.start.getTime() - b.start.getTime())[0];

    if (nextEvent) {
        selectedEvent.value = nextEvent;
    }
};

onMounted(async () => {
    await Promise.all(props.files.map(file => loadICS(file)));

    if (currentMonthIndex.value !== -1) {
        currentPage.value = currentMonthIndex.value;
    }
    selectNextUpcomingEvent();
});

const formatDateTime = (date: Date) => {
    if (!date) return 'No Date';

    const dateFormatter = new Intl.DateTimeFormat('en-GB', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });

    const timeFormatter = new Intl.DateTimeFormat('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: hour12.value
    });

    return `${dateFormatter.format(date)}, ${timeFormatter.format(date)}`;
};

const getMonthName = (monthIndex: number) => {
    const date = new Date(0, monthIndex - 1);
    return new Intl.DateTimeFormat('en-US', { month: 'long' }).format(date);
};

const currentMonthYear = computed(() => {
    const pageIndex = currentPage.value;
    const eventsArray = groupedEvents.value as [string, Event[]][];

    const dateParts = eventsArray[pageIndex]?.[0]?.split("-");

    if (dateParts) {
        const month = getMonthName(+dateParts[1]);
        const year = dateParts[0];
        return `${month} ${year}`;
    }

    return '';
});

const nextPage = () => {
    if (currentPage.value < groupedEvents.value.length - 1) {
        currentPage.value++;
    }
};
const prevPage = () => {
    if (currentPage.value > 0) {
        currentPage.value--;
    }
};
</script>
<template>
    <!-- Paginator -->
    <div v-if="groupedEvents.length > 0"
        style="display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 16px;">
        <Button icon="pi pi-chevron-left" @click="prevPage" :disabled="currentPage === 0" text rounded />
        <span style="min-width: 150px; text-align: center;">
            {{ currentMonthYear }}
        </span>
        <Button icon="pi pi-chevron-right" @click="nextPage" :disabled="currentPage === groupedEvents.length - 1" text
            rounded />
    </div>

    <!-- Filter Buttons -->
    <div class="">
        <Button label="ALL" icon="pi pi-filter" @click="selectedFilters = []" class="filterButton"
            :class="{ 'p-button-info': selectedFilters.length === 0 }" text />
        <Button v-for="promo in promoList" icon="pi pi-filter" :key="promo" :label="promo.toLowerCase()" @click="toggleFilter(promo)" class="filterButton"
            :class="{ 'p-button-info': selectedFilters.includes(promo) } + ' ' + promo.toLowerCase()" text />
    </div>

    <!-- DataTable -->
    <DataTable :value="groupedEvents[currentPage]?.[1] || []" v-model:selection="selectedEvent" v-model:expandedRows="expandedRows" selectionMode="single"
        dataKey="summary" tableStyle="min-width: 1050px" sortField="start" :sortOrder="1">

        <!-- Paginator Container -->
        <Column expander style="width: 5rem" />
        <Column field="org" header="PROMO">
            <template #body="slotProps">
                <span :class="slotProps.data.org.toLowerCase()">{{ slotProps.data.org.toLowerCase() }}</span>
            </template>
        </Column>
        <Column field="summary" header="EVENT"></Column>
        <Column field="start" header="BEGIN">
            <template #body="slotProps">
                {{ formatDateTime(slotProps.data.start) }}
            </template>
        </Column>
        <Column field="end" header="END">
            <template #body="slotProps">
                {{ formatDateTime(slotProps.data.end) }}
            </template>
        </Column>
        <Column field="location" header="LOCATION"></Column>
        <Column field="details" header="DETAILS">
            <template #body="slotProps">
                <a :href="slotProps.data.details" target="_blank">DETAILS</a>
            </template>
        </Column>

        <!-- Expansion Data -->
        <template #expansion="{ data }">
        <div>
            <h4>{{ data.summary }}</h4>
            <p>Start: {{ data.start }}</p>
            <p>End: {{ data.end }}</p>
        </div>
    </template>
    </DataTable>
</template>

<style scoped>
.filterButton {
    min-width: 75px;
}

:deep(:root) {
    --p-datatable-body-cell-selected-border-color: #a4131370;
}

:deep(.p-datatable-column-sorted),
:deep(.p-datatable-header-cell),
:deep(.p-datatable-selectable-row) {
    background-color: rgba(24, 24, 27, 0.8);
    border-color: rgba(24, 24, 27, 0.4);
}

:deep(.p-datatable-tbody > tr.p-datatable-row-selected) {
    background: #a4131370;
}

:deep(.p-button-text) {
    color: rgba(235, 235, 235, 0.64);
}

:deep(.p-button-text):hover {
    color: rgba(235, 235, 235, 0.64);
}

:deep(.p-button-text.p-button-info) {
    color: rgb(207, 27, 3);
}

:deep(.p-button-text.p-button-info:not(:disabled):hover) {
    color: rgba(235, 235, 235, 0.64);
}
</style>
