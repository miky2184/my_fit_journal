(() => {
  const hasDesktopNote = document.querySelector('.desktop-note');
  if (hasDesktopNote && window.innerWidth < 880) {
    const hint = document.createElement('p');
    hint.className = 'muted';
    hint.textContent = 'Suggerimento: per creare programmi complessi usa schermo desktop.';
    hasDesktopNote.appendChild(hint);
  }

  const sportType = document.getElementById('sport-type');
  const courseWrap = document.getElementById('course-wrap');
  const phaseBlock = document.getElementById('phase-block');

  const phaseType = document.getElementById('phase-type');
  const phaseDurationWrap = document.getElementById('phase-duration-wrap');
  const phaseDurationValue = document.getElementById('phase-duration-value');
  const phaseDurationType = document.getElementById('phase-duration-type');
  const phaseRepeatCount = document.getElementById('phase-repeat-count');

  const runningIntensityModeWrap = document.getElementById('phase-running-intensity-mode-wrap');
  const runningIntensityMode = document.getElementById('phase-running-intensity-mode');
  const runningIntensityValueWrap = document.getElementById('phase-running-intensity-value-wrap');
  const runningIntensityValue = document.getElementById('phase-running-intensity-value');

  const swimStyleWrap = document.getElementById('phase-swim-style-wrap');
  const swimStyle = document.getElementById('phase-swim-style');
  const swimEquipmentWrap = document.getElementById('phase-swim-equipment-wrap');
  const swimEquipment = document.getElementById('phase-swim-equipment');

  const gymExerciseWrap = document.getElementById('phase-gym-exercise-wrap');
  const gymExercise = document.getElementById('phase-gym-exercise');
  const gymRepsWrap = document.getElementById('phase-gym-reps-wrap');
  const gymReps = document.getElementById('phase-gym-reps');
  const gymWeightWrap = document.getElementById('phase-gym-weight-wrap');
  const gymWeight = document.getElementById('phase-gym-weight');

  const exOptions = document.getElementById('exercise-options');
  const catalogDataNode = document.getElementById('exercise-catalog-data');

  const phasesJsonInput = document.getElementById('phases-json');
  const phaseList = document.getElementById('phase-list');
  const addPhaseBtn = document.getElementById('add-phase');
  const muscleRoot = document.getElementById('muscle-react-root');

  let phases = [];

  const phaseTypeBySport = {
    running: ['riscaldamento', 'corsa', 'recupero', 'riposo', 'defaticamento'],
    swimming: ['riscaldamento', 'nuoto', 'recupero', 'defaticamento'],
    gym: ['riscaldamento', 'allenamento', 'defaticamento', 'recupero'],
    course: [],
  };

  const catalog = (() => {
    if (!catalogDataNode) return [];
    try {
      const parsed = JSON.parse(catalogDataNode.textContent || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
      return [];
    }
  })();

  const normalize = (value) => (value || '').trim().toLowerCase();
  const currentSport = () => sportType?.value || 'gym';
  const catalogForSport = (sport) => catalog.filter((item) => item.sport_type === sport);
  const findCatalogExercise = (name, sport) => {
    const val = normalize(name);
    if (!val) return null;
    return catalogForSport(sport).find((item) => normalize(item.name) === val) || null;
  };

  const emitMuscleZones = (previewZone = null) => {
    if (!muscleRoot) return;
    const zones = phases.map((ph) => ph.body_zone).filter(Boolean);
    if (previewZone) zones.push(previewZone);
    document.dispatchEvent(new CustomEvent('myfit:exercise-zones-changed', { detail: { zones } }));
  };

  const fillPhaseTypeOptions = () => {
    if (!phaseType || !sportType) return;
    const options = phaseTypeBySport[currentSport()] || [];
    phaseType.innerHTML = '';
    options.forEach((value) => {
      const opt = document.createElement('option');
      opt.value = value;
      opt.textContent = value.charAt(0).toUpperCase() + value.slice(1);
      phaseType.appendChild(opt);
    });
  };

  const renderExerciseAutocomplete = () => {
    if (!exOptions) return;
    exOptions.innerHTML = '';
    catalogForSport(currentSport()).forEach((item) => {
      const option = document.createElement('option');
      option.value = item.name;
      exOptions.appendChild(option);
    });
  };

  const showSportSpecificInputs = () => {
    if (!sportType) return;
    const sport = currentSport();
    const isCourse = sport === 'course';
    const isRunning = sport === 'running';
    const isSwimming = sport === 'swimming';
    const isGym = sport === 'gym';

    if (courseWrap) courseWrap.classList.toggle('hidden', !isCourse);
    if (phaseBlock) phaseBlock.classList.toggle('hidden', isCourse);
    if (phaseDurationWrap) phaseDurationWrap.classList.toggle('hidden', isGym);

    [runningIntensityModeWrap, runningIntensityValueWrap].forEach((el) => el?.classList.toggle('hidden', !isRunning));
    [swimStyleWrap, swimEquipmentWrap].forEach((el) => el?.classList.toggle('hidden', !isSwimming));
    [gymExerciseWrap, gymRepsWrap, gymWeightWrap].forEach((el) => el?.classList.toggle('hidden', !isGym));

    fillPhaseTypeOptions();
    renderExerciseAutocomplete();

    if (phaseDurationType) {
      if (isSwimming) {
        phaseDurationType.innerHTML = '<option value="time">Tempo (min)</option><option value="meters">Metri</option>';
      } else if (isRunning) {
        phaseDurationType.innerHTML = '<option value="time">Tempo (min)</option><option value="meters">Metri</option><option value="kilometers">Kilometri</option>';
      } else {
        phaseDurationType.innerHTML = '<option value="time">Tempo (min)</option>';
      }
    }

    if (!isGym && gymExercise) gymExercise.value = '';
    emitMuscleZones();
  };

  const phaseToLabel = (phase) => {
    const chunks = [`${phase.phase_type}`];
    if (phase.duration_value && phase.duration_type) chunks.push(`${phase.duration_value} (${phase.duration_type})`);
    if (phase.intensity_value) chunks.push(`intensita ${phase.intensity_value}`);
    if (phase.swim_style) chunks.push(`stile ${phase.swim_style}`);
    if (phase.equipment) chunks.push(`attrezzatura ${phase.equipment}`);
    if (phase.exercise_name) chunks.push(`esercizio ${phase.exercise_name}`);
    if (phase.reps) chunks.push(`reps ${phase.reps}`);
    if (phase.weight_kg) chunks.push(`kg ${phase.weight_kg}`);
    if (phase.repeat_count && phase.repeat_count > 1) chunks.push(`x${phase.repeat_count}`);
    return chunks.join(' - ');
  };

  const renderPhaseList = () => {
    if (!phaseList || !phasesJsonInput) return;
    phasesJsonInput.value = JSON.stringify(phases);
    phaseList.innerHTML = '';

    phases.forEach((phase, idx) => {
      const li = document.createElement('li');
      li.className = 'exercise-item';
      li.innerHTML = `<span><strong>Fase ${idx + 1}</strong> - ${phaseToLabel(phase)}</span>`;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'danger small-btn';
      btn.textContent = 'Rimuovi';
      btn.addEventListener('click', () => {
        phases.splice(idx, 1);
        renderPhaseList();
        emitMuscleZones();
      });

      li.appendChild(btn);
      phaseList.appendChild(li);
    });
  };

  const clearPhaseInputs = () => {
    if (phaseDurationValue) phaseDurationValue.value = '';
    if (phaseRepeatCount) phaseRepeatCount.value = '1';
    if (runningIntensityValue) runningIntensityValue.value = '';
    if (gymExercise) gymExercise.value = '';
    if (gymReps) gymReps.value = '';
    if (gymWeight) gymWeight.value = '';
  };

  const readPhaseFromForm = () => {
    if (!sportType || !phaseType) return null;
    const sport = currentSport();

    const needsDuration = sport === 'running' || sport === 'swimming';
    const durationValue = (phaseDurationValue?.value || '').trim();
    if (needsDuration && !durationValue) {
      window.alert('Inserisci la durata della fase.');
      return null;
    }

    const phase = {
      phase_type: phaseType.value,
      duration_type: needsDuration ? (phaseDurationType?.value || 'time') : null,
      duration_value: needsDuration ? durationValue : null,
      repeat_count: Number(phaseRepeatCount?.value || 1) || 1,
      body_zone: sport === 'gym' ? null : 'full_body',
    };

    if (sport === 'running') {
      phase.intensity_mode = runningIntensityMode?.value || 'pace';
      phase.intensity_value = (runningIntensityValue?.value || '').trim() || null;
    }

    if (sport === 'swimming') {
      phase.swim_style = swimStyle?.value || 'stile libero';
      phase.equipment = swimEquipment?.value || 'nessuno';
    }

    if (sport === 'gym') {
      const selected = findCatalogExercise(gymExercise?.value || '', 'gym');
      if (!selected) {
        window.alert('Seleziona un esercizio valido dal catalogo.');
        return null;
      }
      phase.exercise_catalog_id = selected.id;
      phase.exercise_name = selected.name;
      phase.body_zone = selected.body_zone;
      phase.reps = Number(gymReps?.value || 0) || null;
      phase.weight_kg = Number(gymWeight?.value || 0) || null;
    }

    return phase;
  };

  if (sportType) {
    sportType.addEventListener('change', showSportSpecificInputs);
    showSportSpecificInputs();
  }

  if (gymExercise) {
    const syncPreview = () => {
      const selected = findCatalogExercise(gymExercise.value, 'gym');
      emitMuscleZones(selected ? selected.body_zone : null);
    };
    gymExercise.addEventListener('input', syncPreview);
    gymExercise.addEventListener('change', syncPreview);
  }

  if (addPhaseBtn) {
    addPhaseBtn.addEventListener('click', () => {
      const phase = readPhaseFromForm();
      if (!phase) return;
      phases.push(phase);
      renderPhaseList();
      emitMuscleZones();
      clearPhaseInputs();
    });
  }

  const todayWorkout = document.getElementById('today-workout');
  const todayScheduleId = document.getElementById('today-schedule-id');
  const syncTodaySchedule = () => {
    if (!todayWorkout || !todayScheduleId) return;
    const option = todayWorkout.options[todayWorkout.selectedIndex];
    todayScheduleId.value = option?.dataset?.scheduleId || '';
  };
  if (todayWorkout) {
    todayWorkout.addEventListener('change', syncTodaySchedule);
    syncTodaySchedule();
  }

  const recurrenceType = document.getElementById('recurrence-type');
  const recurrenceDaysWrap = document.getElementById('recurrence-days-wrap');
  const endModeWrap = document.getElementById('end-mode-wrap');
  const endMode = document.getElementById('end-mode');
  const endWeeksWrap = document.getElementById('end-weeks-wrap');
  const endDateWrap = document.getElementById('end-date-wrap');

  const toggleRecurrenceBlocks = () => {
    if (!recurrenceType) return;
    const weekly = recurrenceType.value === 'weekly';
    recurrenceDaysWrap?.classList.toggle('hidden', !weekly);
    endModeWrap?.classList.toggle('hidden', !weekly);
    if (!weekly) {
      endWeeksWrap?.classList.add('hidden');
      endDateWrap?.classList.add('hidden');
      return;
    }
    const mode = endMode?.value || 'none';
    endWeeksWrap?.classList.toggle('hidden', mode !== 'weeks');
    endDateWrap?.classList.toggle('hidden', mode !== 'date');
  };

  recurrenceType?.addEventListener('change', toggleRecurrenceBlocks);
  endMode?.addEventListener('change', toggleRecurrenceBlocks);
  toggleRecurrenceBlocks();

  document.querySelectorAll('.calendar-day-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const selected = btn.dataset.date;
      const startDateInput = document.getElementById('schedule-start-date');
      if (startDateInput && selected) {
        startDateInput.value = selected;
      }

      if (recurrenceType?.value === 'weekly') {
        const d = new Date(`${selected}T00:00:00`);
        if (!Number.isNaN(d.getTime())) {
          const jsDay = d.getDay();
          const mondayBased = (jsDay + 6) % 7;
          const checks = document.querySelectorAll('input[name="recurrence_days"]');
          checks.forEach((ck) => {
            ck.checked = String(mondayBased) === ck.value;
          });
        }
      }
    });
  });

  const modal = document.getElementById('delete-series-modal');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');
  const modalSingleBtn = document.getElementById('modal-single-btn');
  const modalSeriesBtn = document.getElementById('modal-series-btn');

  const closeModal = () => {
    if (!modal) return;
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    modal.dataset.pendingForm = '';
  };

  const openModalForForm = (targetForm) => {
    if (!modal) return;
    if (!targetForm.id) {
      targetForm.id = `remove-form-${Math.random().toString(36).slice(2, 10)}`;
    }
    modal.dataset.pendingForm = targetForm.id;
    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
  };

  const submitWithScope = (scope) => {
    if (!modal) return;
    const formId = modal.dataset.pendingForm;
    if (!formId) return closeModal();
    const targetForm = document.getElementById(formId);
    if (!targetForm) return closeModal();
    const scopeInput = targetForm.querySelector('.scope-input');
    if (!scopeInput) return closeModal();
    scopeInput.value = scope;
    closeModal();
    targetForm.submit();
  };

  modalCancelBtn?.addEventListener('click', closeModal);
  modalSingleBtn?.addEventListener('click', () => submitWithScope('single'));
  modalSeriesBtn?.addEventListener('click', () => submitWithScope('series'));
  modal?.addEventListener('click', (event) => {
    if (event.target === modal) closeModal();
  });

  document.querySelectorAll('.calendar-remove-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      const recurring = form.dataset.recurring === '1';
      const scopeInput = form.querySelector('.scope-input');
      if (!scopeInput) return;

      if (!recurring) {
        scopeInput.value = 'single';
        return;
      }

      event.preventDefault();
      openModalForForm(form);
    });
  });

  emitMuscleZones();
})();
