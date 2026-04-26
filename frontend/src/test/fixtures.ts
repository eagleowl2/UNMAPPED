import { mockParse } from '@/lib/mock';
import type { ParseResponse } from '@/lib/types';

/**
 * Canonical fixtures for tests. We deliberately go through `mockParse` so a
 * change to the mock reshape never silently drifts from what tests assert.
 */
export const ghAmara: ParseResponse = mockParse(
  'My name is Amara, I fix phones in Accra, speak Twi English Ga, learned coding on YouTube',
  'GH',
);

export const amAni: ParseResponse = mockParse(
  'Իմ անունը Անի է, Գյումրիից եմ, անգլերեն դասեր եմ տալիս',
  'AM',
);
