<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Button from 'primevue/button';
import Popover from 'primevue/popover';
import Checkbox from 'primevue/checkbox';
import Menu from 'primevue/menu';
import ical from 'ical';
import 'primeicons/primeicons.css';
import { FilterMatchMode } from '@primevue/core/api';

interface CombatEvent {
  url: string;
  organization: string;
  title: string;
  date: string;
  description: string | null;
  broadcast: string[] | null;
  venue: string | null;
  category: string;
  cards: EventCards;
  last_updated: string;
}

interface EventCards {
  main_card?: CardDetails;
  prelims?: CardDetails;
}

interface CardDetails {
  start: string | null;
  end: string | null;
}

const props = defineProps<{
    json_files: string[];
    years: number[]
}>();

const events = ref<CombatEvent[]>([]);
const selectedEvent = ref<CombatEvent | null>(null);
const expandedRows = ref<CombatEvent[]>([]);
const currentPage = ref(0);
const selectedFilters = ref<string[]>([]);
const filterPopover = ref();
const allSelected = ref(false);
const hour12 = ref(false);
const darkmode = ref(false);
const isSmallScreen = ref(false);
const menu = ref();
const items = ref([
    {
        label: 'Filter',
        items: [
            {
                label: 'Refresh',
                icon: 'pi pi-refresh'
            },
            {
                label: 'Export',
                icon: 'pi pi-upload'
            }
        ]
    }
]);

const loadJSON = async (file: string) => {
    try {
        const results = await Promise.allSettled(
            props.years.map(async (year) => {
                const response = await fetch(`https://raw.githubusercontent.com/LeanderWernst/combat-sports-event-scraper/refs/heads/main/json/${year}/${file}`);
                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status}`);
                }
                return await response.json();
            })
        );

        results.forEach((result, index) => {
            const year = props.years[index];
            if (result.status === "fulfilled") {
                const data = result.value;
                if (Array.isArray(data)) {
                    events.value.push(...data);
                } else {
                    console.error(`Unexpected JSON format for year ${year}:`, data);
                }
            } else {
                //console.warn(`Failed to fetch JSON for year ${year}. It is probably just absent.:`, result.reason);
            }
        });
    } catch (error) {
        console.error("Unexpected error during JSON loading:", error);
    }
};



const groupedEvents = computed(() => {
    const groups = new Map<string, CombatEvent[]>();

    // Group events by month key
    events.value.forEach(event => {
        const monthKey = event.date.slice(0,7);
        if (!groups.has(monthKey)) {
            groups.set(monthKey, []);
        }
        groups.get(monthKey)?.push(event);
    });

    // Filter events based on selected filters
    const filteredEvents = selectedFilters.value.length > 0
        ? events.value.filter(event => selectedFilters.value.includes(event.organization))
        : events.value;

    // Filter events but maintain empty groups
    const filteredGroups = new Map<string, CombatEvent[]>();
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

const togglePopover = (event: Event) => {
    filterPopover.value.toggle(event);
};

// Alle Filter ein-/ausschalten
const toggleAllFilters = () => {
    if (allSelected.value) {
        selectedFilters.value = [...promoList.value];
    } else {
        selectedFilters.value = [];
    }
};

const promoList = computed(() => {
    return Array.from(new Set(events.value.map(event => event.organization)));
});

const selectNextUpcomingEvent = () => {
    const now = new Date();
    const currentGroupedEvents = groupedEvents.value[currentPage.value]?.[1] || [];

    let nextEvent: typeof currentGroupedEvents[0] | null = null;
    let minTimeDifference = Infinity;

    for (const event of currentGroupedEvents) {
        const mainStart = new Date(event.cards.main_card!.start!);
        const mainEnd = new Date(event.cards.main_card!.end!);

        // calculate and save the smallest time difference to future event
        if (mainStart >= now && mainEnd > now) {
            const timeDifference = mainStart.getTime() - now.getTime();
            if (timeDifference < minTimeDifference) {
                nextEvent = event;
                minTimeDifference = timeDifference;
            }
        }
    }

    if (nextEvent) {
        selectedEvent.value = nextEvent;
    }
};

onMounted(async () => {
    await Promise.all(props.json_files.map(file => loadJSON(file)));

    if (currentMonthIndex.value !== -1) {
        currentPage.value = currentMonthIndex.value;
    }

    selectNextUpcomingEvent();

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);

    //setUniformRowHeight();
});

onBeforeUnmount(() => {
    window.removeEventListener('resize', checkScreenSize);
});

function checkScreenSize() {
    isSmallScreen.value = window.innerWidth <= 768;
}

function setUniformRowHeight() {
    nextTick(() => {
        const rows = document.querySelectorAll('.p-datatable-tbody > tr');
        if (rows.length > 0) {
            const maxHeight = Math.max(
                ...Array.from(rows).map(row => (row as HTMLElement).offsetHeight)
            );

            Array.from(rows).forEach(row => {
                (row as HTMLElement).style.height = `${maxHeight}px`;
            });
        }
    });
}

function handleRowSelect(event: CombatEvent) {
    selectedEvent.value = event;
}


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

    return `${dateFormatter.format(date).replace(",", "")} ${timeFormatter.format(date).replace(",", "")}`;
};

const formatDateTimeArray = (date: Date) => {
    if (!date) return ["n/a"];

    return formatDateTime(date).split(" ");
}

const getMonthName = (monthIndex: number) => {
    const date = new Date(0, monthIndex - 1);
    return new Intl.DateTimeFormat('en-US', { month: 'long' }).format(date);
};

const currentMonthYear = computed(() => {
    const pageIndex = currentPage.value;
    const eventsArray = groupedEvents.value as [string, CombatEvent[]][];

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
    <div v-if="groupedEvents.length > 0" style="display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 16px;">
        <Button icon="pi pi-chevron-left" @click="prevPage" :disabled="currentPage === 0" text rounded />
        <span style="min-width: 150px ; text-align: center; font-size: 1rem;">
            {{ currentMonthYear }}
        </span>
        <Button icon="pi pi-chevron-right" @click="nextPage" :disabled="currentPage === groupedEvents.length - 1" text
            rounded />
    </div>

    <!-- Filter Button -->
    <div class="filter-container">

    <!-- Popover Container -->
    <Popover ref="filterPopover" id="filter_popover">
        <div class="filter-panel" @click.stop>
            <h4>SELECT FILTER</h4>
            <div class="filter-options">
                <div v-for="promo in promoList" :key="promo" class="filter-option">
                    <Checkbox 
                        class="checkbox"
                        :inputId="promo" 
                        :value="promo"
                        v-model="selectedFilters"
                    />
                    <label :for="promo" :class="promo != 'One Championship' ? promo : 'one'">{{ promo }}</label>
                </div>
                <div style="display: flex; justify-content: center;">
                    <Button 
                        icon="pi pi-filter-slash"
                        label="RESET" 
                        @click="toggleAllFilters" 
                        class="reset-filter"
                    />
                </div>
            </div>
        </div>
    </Popover>
    </div>
    <!-- TODO: Implement Button marking next upcoming event -->
    <!-- DataTable -->
    <DataTable 
        :class="isSmallScreen ? '' : 'table-fixed-layout'"
        :value="groupedEvents[currentPage]?.[1] || []"
        v-model:selection="selectedEvent"
        v-model:expandedRows="expandedRows"
        @rowExpand="handleRowSelect"
        selectionMode="single"
        dataKey="url"
        tableStyle="width: 100%;"
        sortField="cards.main_card.start"
        :sortOrder="1"
        scrollable
        scrollHeight="65vh"
    >
        <!-- Paginator Container -->
        <Column expander style="width: 3%; text-align: center;" >
            <template #header >
                <Button 
                    type="button"
                    class="filter-button"
                    icon="pi pi-filter" 
                    @click="togglePopover" 
                    aria-haspopup="true" 
                    aria-controls="filter_popover" 
                />
            </template>
        </Column>
        <Column v-if="!isSmallScreen" field="org" header="PROMO" style="width: 8%;">
            <template #body="slotProps">
                <span :class="slotProps.data.organization.split(' ')[0].toLowerCase()">{{ slotProps.data.organization.split(' ')[0].toLowerCase() }}</span>
            </template>
        </Column>
        <Column field="title" header="EVENT" style="width:29%;"></Column>
        <Column field="start" header="BEGIN" style="width:29%; padding: 0.8rem">
            <template #body="slotProps">
                {{ formatDateTime(new Date(slotProps.data.cards.main_card.start)) }}
                <!-- <table class="time-info-table">
                    <tbody>
                        <tr>
                            <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.start))[0] }}</td>
                            <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.start))[1] }}</td>
                            <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.start))[2] }}</td>
                        </tr>
                    </tbody>
                </table> -->
            </template>
        </Column>
        <!-- <Column field="end" header="END" style="width:13%; min-width: 150px;">
            <template #body="slotProps">
                <table class="time-info-table">
                    <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.end))[0] }}</td>
                    <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.end))[1] }}</td>
                    <td>{{ formatDateTimeArray(new Date(slotProps.data.cards.main_card.end))[2] }}</td>
                </table>
            </template>
        </Column> -->
        <Column v-if="!isSmallScreen" field="venue" header="LOCATION" style="width: 29%;"></Column>
        <Column field="details" style="width: 2%; text-align: center;">
            <template #header style="justify-content: center; padding: 0;">
                <span class="p-datatable-column-title" style="text-align: center;">URL</span>
            </template>
            <template #body="slotProps">
                <a :href="slotProps.data.url" target="_blank" class="p-link" style="padding: 0;">
                    <i class="pi pi-external-link"></i>
                </a>
            </template>
        </Column>

        <!-- Expansion Data -->
        <template #expansion="{ data }">
        <div>
            <h2>{{ data.title }}</h2>
            <hr>
            <p v-if="data.cards.prelims.start">
                PRELIMS<br>
                Start: {{ new Date(data.cards.prelims.start).toLocaleString('en-GB').slice(0,-3) }}<br>
                End: {{ new Date(data.cards.prelims.end).toLocaleString('en-GB').slice(0,-3) }}
            </p>
            <br v-if="data.cards.prelims.start">
            <p>
                MAIN CARD<br>
                Start: {{ new Date(data.cards.main_card.start).toLocaleString('en-GB').slice(0,-3) }}<br>
                End: {{ new Date(data.cards.main_card.end).toLocaleString('en-GB').slice(0,-3) }}
            </p>
        </div>
    </template>
    </DataTable>
</template>

<style scoped>
.filterButton {
    min-width: 75px;
}

.table-fixed-layout {
    table-layout: fixed;
}

a {
    border-radius: 10px;
    padding: 2px 10px;
}

a:hover {
    background-color: rgba(150, 149, 150, 0.2);
}

.filter-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 10px;
    min-width: 200px;
}

.filter-option {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-button {
    border-radius: 25px;
    background-color: rgb(207, 27, 3);
    border-color: rgb(207, 27, 3);
    color: white;
}

.reset-filter {
  background: transparent;
  border-color: transparent;
  color: #eb2727;
}

.reset-filter:not(:disabled):hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: transparent;
  color: #d45252;
}

.checkbox input {
    border-radius: 25px !important;
}

table.time-info-table {
    display: flex;
    justify-content: space-between;
}

table.time-info-table td {
    margin: 0 2px;
}

:deep(:root) {
    --p-datatable-body-cell-selected-border-color: #a4131370;
}

:deep(.p-datatable-table-container) {
    border-radius: 25px;
}

:deep(.p-datatable-column-sorted),
:deep(.p-datatable-header-cell),
:deep(.p-datatable-selectable-row) {
    background-color: rgba(24, 24, 27, 0.8);
    border-color: rgba(24, 24, 27, 0.4);
}

:deep(.p-datatable-column-sorted),
:deep(.p-datatable-selectable-row) {
    height: 75px;
}

:deep(.p-datatable-thead > tr > th:first-child > div) {
    justify-content: center;
}

:deep(.p-datatable-thead > tr > th:last-child > div) {
    justify-content: center;
}

:deep(.p-datatable-tbody > tr.p-datatable-row-selected) {
    background: #a4131370;
}

:deep(.p-datatable-tbody > tr > td) {
    font-size: 1em;
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
