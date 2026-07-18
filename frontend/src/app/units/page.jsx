"use client";

import PageHero from "@/components/PageHero";
import { UNIT_PAGE_COPY } from "@/CONSTANTS";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getAllUnits, createUnit } from "@/api.js";
import PageSection  from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import GenericForm from "@/components/GenericForm";
import UnitList from "@/components/UnitList";


export default function UnitsPage() {
    const [units, setUnits] = useState([]);
    const [unitsQueryState, setUnitsQueryState] = useState({
        "loading": false,
        "error": ""
    });
    const [unitFormState, setUnitFormState] = useState({
        "unitName": "",
        "unitSymbol": ""
    });
    const setUnitName = (event) => setUnitFormState(prevState => ({...prevState, "unitName": event.target.value}));
    const setUnitSymbol = (event) => setUnitFormState(prevState => ({...prevState, "unitSymbol": event.target.value}));

    const loadUnits = useCallback(async () => {
        try{
            const units = await getAllUnits();
            setUnits(units);
        } catch(loadError) {
            setUnitsQueryState(prevState => ({...prevState, "error": loadError.message || "Units could not be loaded. Please try again"}));
        } finally {
            setUnitsQueryState(prevState => ({...prevState, "loading": false}));
        }
    });

    useEffect(() => {
        loadUnits();
    }, [loadUnits]);

    const summaryValue = useMemo(() => {
        if(units.length === 0)
            return "0";
        
        return units.length.toString()
    }, [units]);

    return (
        <div className="space-y-8">
            <PageHero
                badge={UNIT_PAGE_COPY.badge}
                title={UNIT_PAGE_COPY.heading}
                description={UNIT_PAGE_COPY.description}
                summaryValue={summaryValue}
                summaryLabel={UNIT_PAGE_COPY.countLabel}
            />

            <PageSection>
                <SectionCard title={UNIT_PAGE_COPY.createSectionTitle} description={UNIT_PAGE_COPY.createSectionDescription}>
                    <GenericForm
                        submitBtnLabel={UNIT_PAGE_COPY.createUnitBtnLabel}
                        submitSuccessMsg={UNIT_PAGE_COPY.submitSuccessMsg}
                        helperText={UNIT_PAGE_COPY.helperText}
                        onSubmit={async (event) => {
                            event.preventDefault();
                            await createUnit(unitFormState.unitName, unitFormState.unitSymbol);
                        }}
                        controls={
                            [
                                {
                                    "label": "Unit Name",
                                    "type": "text",
                                    "value": unitFormState.unitName,
                                    "required": true,
                                    "onValueChange": setUnitName
                                },
                                {
                                    "label": "Unit Symbol",
                                    "type": "text",
                                    "value": unitFormState.unitSymbol,
                                    "required": true,
                                    "onValueChange": setUnitSymbol
                                }
                            ]
                        }
                    />
                </SectionCard>

                <SectionCard title={UNIT_PAGE_COPY.heading} description={UNIT_PAGE_COPY.description}>
                    <UnitList
                        units={units}
                        isLoading={unitsQueryState.loading}
                        error={unitsQueryState.error}
                        emptyTitle={UNIT_PAGE_COPY.emptyTitle}
                        emptyMessage={UNIT_PAGE_COPY.emptyMessage}
                    />
                </SectionCard>
            </PageSection>
        </div>
    );
}