# Source and license

Magic's resource mapping, calendar, managed-font and Band9 background cores,
and the corresponding regression models, are adapted from the user's Corona
resource module under AGPL-3.0. Existing license terms remain in LICENSE.

Magic adds Chem ABI 2 registration, native UI, package storage and validation,
ChemConnect control, and firmware 3.1.35 adapters. The earlier manager,
watchface installer, directory layout and other-device adapters are not build
dependencies. Chem's SDK is supplied by the adjacent Chem checkout.

Glaze UI artwork in examples/glazeui is adapted from GlazeUI v1.0.2 by
山荼skat, supplied locally by the user. Attribution and artwork rights remain
with the original author; Magic's code license does not grant additional
rights to redistribute these third-party assets. The resource conversion
helper uses corona-core 0.2.5 (MIT) through Cargo without vendoring its code.
