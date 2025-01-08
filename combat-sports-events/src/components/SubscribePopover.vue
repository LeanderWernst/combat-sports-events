<script setup lang="ts">
import { ref, defineProps } from 'vue';
import { InputGroup, InputGroupAddon, InputText, Button, Popover } from 'primevue';
import 'primeicons/primeicons.css';
import { useToast } from "primevue/usetoast";

const props = defineProps<{
    file: string;
}>();

const promoTitle = props.file.split("_")[0]
const popover = ref();
const toggle = (event: any) => {
    popover.value.toggle(event);
}
const link = !props.file.includes("one_events.ics")
             ? ref(`https://raw.githubusercontent.com/LeanderWernst/combat-sports-event-scraper/refs/heads/main/ics/${props.file}`)
             : ref("https://calendar.onefc.com/ONE-Championship-events.ics");
const toast = useToast();

const copyToClipboard = () => {
    if (link.value) {
        navigator.clipboard.writeText(link.value)
            .then(() => show("Success", "Link copied to clipboard."))
            .catch(err => console.error("Failed to copy: ", err));
    }
};

const downloadFile = async () => {
    try {
        let url;
        
        if (!props.file.includes("one_events.ics")) {
            const response = await fetch(link.value);
            if (!response.ok) throw new Error("File download failed.");
    
            const blob = await response.blob();
            url = window.URL.createObjectURL(blob);
        }

        const anchor = document.createElement('a');
        anchor.href = url ? url : link.value;
        anchor.download = promoTitle.toLowerCase() + "_events.ics";

        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);

        if (!props.file.includes("one_events.ics") && url) {
            window.URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error("Error downloading file:", error);
    }
};


const show = (infoHeadline: string, messageContent: string, lifeMiliseconds: number = 3000) => {
    toast.add({ severity: 'info', summary: infoHeadline, detail: messageContent, life: lifeMiliseconds });
};
</script>

<template>
    <div class="">
        <Button type="button" :class=promoTitle class="subscribeButton" icon="pi pi-calendar" :label=promoTitle
            @click="toggle" />

        <Popover ref="popover">
            <div class="popover">
                <div>
                    <span class="red">Subscribe to ICS</span>
                    <p class="grey">Copy the link and paste it in your calendar app to subscribe.<br>Alternatively
                        download the ics file. Downloaded files will not update themselves.</p>
                    <InputGroup>
                        <InputText :value=link readonly class="filepath"></InputText>
                        <InputGroupAddon @click="copyToClipboard" class="inputGroupAddon">
                            <i class="pi pi-copy"></i>
                        </InputGroupAddon>
                        <InputGroupAddon @click="downloadFile" class="inputGroupAddon">
                            <i class="pi pi-download"></i>
                        </InputGroupAddon>
                    </InputGroup>
                </div>
            </div>
        </Popover>
    </div>
</template>

<style scoped>
.filepath {
    font-family: 'Courier New', Courier, monospace;
}

.inputGroupAddon {
    cursor: pointer;
}

.inputGroupAddon:hover {
    background-color: rgb(50, 50, 50);
}

:deep(.p-button.subscribeButton) {
    color: #fff;
    background-color: rgb(207, 27, 3);
    border-color: rgb(207, 27, 3);
}
:deep(.p-button.subscribeButton):hover {
    background-color: #6f0000;
    border-color: #6f0000;
}
</style>