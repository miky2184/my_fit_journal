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
  const bodyMap = document.getElementById('body-map');

  let exercises = [];

  const showOrHideSportBlocks = () => {
    if (!sportType) return;
    const sport = sportType.value;
    const isCourse = sport === 'course';

    if (courseWrap) courseWrap.classList.toggle('hidden', !isCourse);
    if (detailedBlock) detailedBlock.classList.toggle('hidden', isCourse);

    if (exObjectiveLabel) {
      exObjectiveLabel.childNodes[0].nodeValue = `${objectiveBySport[sport] || 'Obiettivo'} `;
    }
  };

  const showOrHideRecurrence = () => {
    if (!recurrenceType || !repeatWeeksWrap) return;
    repeatWeeksWrap.classList.toggle('hidden', recurrenceType.value !== 'weekly');
  };

  const renderBodyMap = () => {
    if (!bodyMap) return;
    const zones = new Set(exercises.map((ex) => ex.body_zone));
    bodyMap.querySelectorAll('.zone').forEach((el) => {
      el.classList.remove('active');
      if (zones.has('full_body')) {
        el.classList.add('active');
        return;
      }

      const classList = Array.from(el.classList);
      const match = classList.some((cls) => zones.has(cls));
      if (match) {
        el.classList.add('active');
      }
    });
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
        renderBodyMap();
      });

      li.appendChild(btn);
      exerciseList.appendChild(li);
    });
  };

  const readExerciseFromForm = () => {
    const name = document.getElementById('ex-name')?.value?.trim() || '';
    if (!name) return null;

    const mode = document.getElementById('ex-mode')?.value || 'single';
    const sets = Number(document.getElementById('ex-sets')?.value || 0) || null;
    const reps = Number(document.getElementById('ex-reps')?.value || 0) || null;
    const durationMinutes = Number(document.getElementById('ex-duration')?.value || 0) || null;
    const objective = document.getElementById('ex-objective')?.value?.trim() || null;
    const bodyZone = document.getElementById('ex-zone')?.value || 'full_body';

    return {
      name,
      mode,
      sets,
      reps,
      duration_minutes: durationMinutes,
      objective,
      body_zone: bodyZone,
    };
  };

  const clearExerciseForm = () => {
    ['ex-name', 'ex-sets', 'ex-reps', 'ex-duration', 'ex-objective'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
  };

  if (sportType) {
    sportType.addEventListener('change', showOrHideSportBlocks);
    showOrHideSportBlocks();
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
      renderBodyMap();
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
})();
