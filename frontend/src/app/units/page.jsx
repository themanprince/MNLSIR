"use client";

import PageHero from "@/components/PageHero";
import { UNIT_PAGE_COPY } from "@/CONSTANTS";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getAllUnits, createUnit } from "@/api.js";
import PageSection  from "@/components/PageSection";
import SectionCard from "@/components/SectionCard";
import GenericForm from "@/components/GenericForm";


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
                badge="Units Catalog"
                title={UNIT_PAGE_COPY.heading}
                description={UNIT_PAGE_COPY.description}
                summaryValue={summaryValue}
                summaryLabel={UNIT_PAGE_COPY.countLabel}
            />

            <PageSection>
                <SectionCard title="Create Unit" description="Add a new unit to the unit registry">
                    <GenericForm
                        submitBtnLabel={"Create Unit"}
                        submitSuccessMsg={"Unit Created Successfully"}
                        helperText={"After creating this unit, you can set conversion rules of products to involve this unit"}
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
            </PageSection>
        </div>
    );
}