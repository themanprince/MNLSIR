"use client";

import PageHero from "@/components/PageHero";
import { UNIT_PAGE_COPY } from "@/CONSTANTS";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useGetUnits } from "@/hooks";
import { createUnit, getAllUnits } from "@/api";
import PageSection  from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import GenericForm from "@/components/GenericForm";
import UnitList from "@/components/UnitList";


export default function UnitsPage() {
    let [units, setUnits, isLoading, error] = useGetUnits();

    const [unitFormState, setUnitFormState] = useState({
        "unitName": "",
        "unitSymbol": ""
    });
    const setUnitName = (event) => setUnitFormState(prevState => ({...prevState, "unitName": event.target.value}));
    const setUnitSymbol = (event) => setUnitFormState(prevState => ({...prevState, "unitSymbol": event.target.value}));

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
                            setUnits(await getAllUnits());
                            setUnitFormState({
                                "unitName": "",
                                "unitSymbol": ""
                            });
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
                        isLoading={isLoading}
                        error={error}
                        emptyTitle={UNIT_PAGE_COPY.emptyTitle}
                        emptyMessage={UNIT_PAGE_COPY.emptyMessage}
                    />
                </SectionCard>
            </PageSection>
        </div>
    );
}