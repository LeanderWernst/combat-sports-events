<script setup lang="ts">
import { ref, defineProps } from 'vue';
import { InputGroup, InputGroupAddon, InputText, Button, Popover } from 'primevue';
import 'primeicons/primeicons.css';

const props = defineProps<{
    file: string;
}>();

const promoTitle = props.file.split("_")[0]
const popover = ref();
const toggle = (event: any) => {
    popover.value.toggle(event);
}
const link = ref(`https://raw.githubusercontent.com/LeanderWernst/combat-sports-event-scraper/refs/heads/main/ics/${props.file}`);

const copyToClipboard = () => {
    if (link.value) {
        navigator.clipboard.writeText(link.value)
            .then(() => alert("Link copied to clipboard"))
            .catch(err => console.error("Failed to copy: ", err));
    }
};

const downloadFile = () => {
    window.open(link.value);
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