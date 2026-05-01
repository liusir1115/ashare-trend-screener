let selectedPlaybookId = null;

export function getSelectedPlaybookId() {
  return selectedPlaybookId;
}

export function setSelectedPlaybookId(playbookId) {
  selectedPlaybookId = playbookId || null;
}

export function syncSelectedPlaybook(strategyData = {}) {
  selectedPlaybookId = strategyData.selected_playbook_id ?? selectedPlaybookId;
}
