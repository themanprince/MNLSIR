import { getAllUnits } from "@/api.js";
import { useCallback, useEffect, useState } from "react";


export function useGetUnits() {
    const [units, setUnits] = useState([]);

    const [unitsQueryState, setUnitsQueryState] = useState({
        "isLoading": false,
        "error": ""
    });

    const loadUnits = useCallback(async () => {
        try{
            setUnitsQueryState(prevState => {
                return {...prevState, "isLoading": true, "error": ""}
            });
            const unitsReturned = await getAllUnits();
            setUnits(prevUnits => unitsReturned);
        } catch(loadError) {
            setUnitsQueryState(prevState => ({...prevState, "error": loadError.message || "Units could not be loaded. Please try again"}));
        } finally {
            setUnitsQueryState(prevState => ({...prevState, "isLoading": false}));
        }
    }, []);

    useEffect(() => {
        loadUnits();
    }, [loadUnits]);

    return [ units, setUnits, unitsQueryState.isLoading, unitsQueryState.error ];
}