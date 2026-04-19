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
  const detailedBlock = document.getElementById('detailed-block');
  const exObjectiveLabel = document.getElementById('ex-objective-label');
  const recurrenceType = document.getElementById('recurrence-type');
  const repeatWeeksWrap = document.getElementById('repeat-weeks-wrap');

  const objectiveBySport = {
    gym: 'Kg target',
    swimming: 'Stile',
    running: 'Zona / passo',
    course: 'Obiettivo',
  };

  const exercisesJsonInput = document.getElementById('exercises-json');
  const exerciseList = document.getElementById('exercise-list');
  const addExerciseBtn = document.getElementById('add-exercise');
  const muscleRoot = document.getElementById('muscle-react-root');

  const exNameInput = document.getElementById('ex-name');
  const exOptions = document.getElementById('exercise-options');
  const exZoneLabel = document.getElementById('ex-zone-label');
  const catalogDataNode = document.getElementById('exercise-catalog-data');

  let exercises = [];

  const catalog = (() => {
    if (!catalogDataNode) return [];
    try {
      const parsed = JSON.parse(catalogDataNode.textContent || '[]');
      if (!Array.isArray(parsed)) return [];
      return parsed;
    } catch (_) {
      return [];
    }
  })();

  const normalize = (value) => (value || '').trim().toLowerCase();

  const catalogForCurrentSport = () => {
    const sport = sportType?.value || 'gym';
    return catalog.filter((item) => item.sport_type === sport);
  };

  const findCatalogByName = (name) => {
    const value = normalize(name);
    if (!value) return null;
    return catalogForCurrentSport().find((item) => normalize(item.name) === value) || null;
  };

  const renderCatalogAutocomplete = () => {
    if (!exOptions) return;
    exOptions.innerHTML = '';
    catalogForCurrentSport().forEach((item) => {
      const option = document.createElement('option');
      option.value = item.name;
      exOptions.appendChild(option);
    });
  };

  const refreshZonePreview = () => {
    if (!exZoneLabel || !exNameInput) return;
    const match = findCatalogByName(exNameInput.value);
    exZoneLabel.value = match ? match.body_zone : '--';
  };

  const showOrHideSportBlocks = () => {
    if (!sportType) return;
    const sport = sportType.value;
    const isCourse = sport === 'course';

    if (courseWrap) courseWrap.classList.toggle('hidden', !isCourse);
    if (detailedBlock) detailedBlock.classList.toggle('hidden', isCourse);

    if (exObjectiveLabel) {
      exObjectiveLabel.childNodes[0].nodeValue = `${objectiveBySport[sport] || 'Obiettivo'} `;
    }

    renderCatalogAutocomplete();
    refreshZonePreview();
  };

  const showOrHideRecurrence = () => {
    if (!recurrenceType || !repeatWeeksWrap) return;
    repeatWeeksWrap.classList.toggle('hidden', recurrenceType.value !== 'weekly');
  };

  const emitMuscleZones = () => {
    if (!muscleRoot) return;
    const zones = exercises.map((ex) => ex.body_zone);
    document.dispatchEvent(
      new CustomEvent('myfit:exercise-zones-changed', {
        detail: { zones },
      }),
    );
  };

  const renderExerciseList = () => {
    if (!exerciseList || !exercisesJsonInput) return;
    exercisesJsonInput.value = JSON.stringify(exercises);
    exerciseList.innerHTML = '';

    exercises.forEach((ex, index) => {
      const li = document.createElement('li');
      li.className = 'exercise-item';
      li.innerHTML = `<span><strong>${ex.name}</strong> - ${ex.mode} - ${ex.objective || '-'} (${ex.body_zone})</span>`;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'danger small-btn';
      btn.textContent = 'Rimuovi';
      btn.addEventListener('click', () => {
        exercises.splice(index, 1);
        renderExerciseList();
        emitMuscleZones();
      });

      li.appendChild(btn);
      exerciseList.appendChild(li);
    });
  };

  const readExerciseFromForm = () => {
    if (!exNameInput) return null;
    const matched = findCatalogByName(exNameInput.value);
    if (!matched) {
      window.alert('Seleziona un esercizio valido dal catalogo suggerito.');
      return null;
    }

    const mode = document.getElementById('ex-mode')?.value || 'single';
    const sets = Number(document.getElementById('ex-sets')?.value || 0) || null;
    const reps = Number(document.getElementById('ex-reps')?.value || 0) || null;
    const durationMinutes = Number(document.getElementById('ex-duration')?.value || 0) || null;
    const objective = document.getElementById('ex-objective')?.value?.trim() || null;

    return {
      exercise_catalog_id: matched.id,
      name: matched.name,
      mode,
      sets,
      reps,
      duration_minutes: durationMinutes,
      objective,
      body_zone: matched.body_zone,
    };
  };

  const clearExerciseForm = () => {
    ['ex-name', 'ex-sets', 'ex-reps', 'ex-duration', 'ex-objective'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    if (exZoneLabel) exZoneLabel.value = '--';
  };

  if (sportType) {
    sportType.addEventListener('change', showOrHideSportBlocks);
    showOrHideSportBlocks();
  }

  if (exNameInput) {
    exNameInput.addEventListener('input', refreshZonePreview);
    exNameInput.addEventListener('change', refreshZonePreview);
  }

  if (recurrenceType) {
    recurrenceType.addEventListener('change', showOrHideRecurrence);
    showOrHideRecurrence();
  }

  if (addExerciseBtn) {
    addExerciseBtn.addEventListener('click', () => {
      const exercise = readExerciseFromForm();
      if (!exercise) return;
      exercises.push(exercise);
      renderExerciseList();
      emitMuscleZones();
      clearExerciseForm();
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

  emitMuscleZones();
})();
